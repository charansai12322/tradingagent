"""Deterministic Pre-Trade Risk Engine.

Enforces institutional-grade risk constraints prior to order execution:
- Global execution kill-switch check
- Strict paper-mode validation
- Explicit Human-in-the-Loop consent
- Maximum order notional limit
- Maximum portfolio position notional limit
- Long-only shorting protection (verifies position ownership for SELL orders)
- Replayed/duplicate approval protection
- Proposal TTL expiry validation
The AI agent CANNOT bypass this layer.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional, Set
import threading

from app.core.config import Settings, get_settings
from app.schemas.trading import (
    OrderApprovalRequest,
    OrderSide,
    OrderStatus,
    PortfolioResponse,
    ProposedOrder,
    RiskCheckResult,
)

logger = logging.getLogger("tradingagent.risk")


class ProposalRegistry:
    """Thread-safe in-memory store for active server-side order proposals."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._proposals: Dict[str, ProposedOrder] = {}
                cls._instance._executed_ids: Set[str] = set()
            return cls._instance

    def register(self, proposal: ProposedOrder) -> None:
        """Store a new order proposal."""
        with self._lock:
            self._proposals[proposal.proposal_id] = proposal
            logger.info("Registered proposal: %s for %s (%s)", proposal.proposal_id, proposal.symbol, proposal.side)

    def get(self, proposal_id: str) -> Optional[ProposedOrder]:
        """Retrieve proposal by ID."""
        with self._lock:
            return self._proposals.get(proposal_id)

    def mark_executed(self, proposal_id: str) -> None:
        """Mark proposal as executed and add to deduplication set."""
        with self._lock:
            if proposal_id in self._proposals:
                self._proposals[proposal_id].status = OrderStatus.EXECUTED
            self._executed_ids.add(proposal_id)

    def is_executed(self, proposal_id: str) -> bool:
        """Check if proposal has already been executed."""
        with self._lock:
            return proposal_id in self._executed_ids


# Singleton registry instance
proposal_registry = ProposalRegistry()


class RiskEngine:
    """Deterministic risk evaluator that validates orders before submission."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def evaluate_approval(
        self,
        approval_req: OrderApprovalRequest,
        portfolio: Optional[PortfolioResponse] = None,
    ) -> tuple[RiskCheckResult, Optional[ProposedOrder]]:
        """Evaluate all risk checks against an approval request."""
        checks: List[str] = []
        rejections: List[str] = []
        now_str = datetime.now(timezone.utc).isoformat()
        proposal_id = approval_req.proposal_id

        # 1. Master Kill-Switch Check
        checks.append("check_trading_enabled")
        if not self.settings.TRADING_ENABLED:
            rejections.append("TRADING_ENABLED is false. Execution is globally disabled by configuration.")

        # 2. Strict Paper Mode Check
        checks.append("check_paper_trading_mode")
        if self.settings.TRADING_MODE.lower() != "paper":
            rejections.append(f"Invalid TRADING_MODE '{self.settings.TRADING_MODE}'. Only paper mode is allowed.")

        # 3. Explicit Human Approval Consent Check
        checks.append("check_explicit_human_approval")
        if not approval_req.confirm:
            rejections.append("Explicit confirmation was declined by user.")

        # 4. Proposal Existence & Status
        checks.append("check_proposal_validity")
        proposal = proposal_registry.get(proposal_id)
        if not proposal:
            rejections.append(f"Proposal '{proposal_id}' not found or never issued by server.")
            return RiskCheckResult(
                passed=False,
                proposal_id=proposal_id,
                checks_performed=checks,
                rejection_reasons=rejections,
                evaluated_at=now_str,
            ), None

        # 5. Replay / Duplicate Execution Protection
        checks.append("check_replay_prevention")
        if proposal_registry.is_executed(proposal_id) or proposal.status == OrderStatus.EXECUTED:
            rejections.append(f"Proposal '{proposal_id}' has already been executed. Duplicate order blocked.")

        # 6. Proposal Expiration Check
        checks.append("check_proposal_expiry")
        try:
            expires_at = datetime.fromisoformat(proposal.expires_at)
            now_check = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now_check > expires_at:
                rejections.append(f"Proposal '{proposal_id}' expired at {proposal.expires_at}.")
        except Exception:
            rejections.append("Malformed proposal expiration timestamp.")

        # 7. Quantity & Order Notional Limits
        checks.append("check_order_notional_limits")
        if proposal.quantity <= 0:
            rejections.append(f"Invalid order quantity: {proposal.quantity}. Must be greater than 0.")

        order_notional = proposal.estimated_notional
        if order_notional > self.settings.MAX_ORDER_NOTIONAL_USD:
            rejections.append(
                f"Order notional ${order_notional:.2f} exceeds MAX_ORDER_NOTIONAL_USD limit (${self.settings.MAX_ORDER_NOTIONAL_USD:.2f})."
            )

        # 8. Portfolio Position Limits & Sell Inventory Check
        checks.append("check_portfolio_constraints")
        if portfolio:
            existing_pos = next(
                (p for p in portfolio.positions if p.symbol.upper() == proposal.symbol.upper()),
                None,
            )

            # If BUY, verify total position notional will not exceed maximum limit
            if proposal.side == OrderSide.BUY:
                current_position_notional = (existing_pos.market_value or 0.0) if existing_pos else 0.0
                projected_position_notional = current_position_notional + order_notional
                if projected_position_notional > self.settings.MAX_POSITION_NOTIONAL_USD:
                    rejections.append(
                        f"Projected position value ${projected_position_notional:.2f} exceeds "
                        f"MAX_POSITION_NOTIONAL_USD (${self.settings.MAX_POSITION_NOTIONAL_USD:.2f})."
                    )

            # If SELL, ensure stock is actually owned in portfolio (prevent naked shorting)
            elif proposal.side == OrderSide.SELL:
                if not existing_pos or existing_pos.qty < proposal.quantity:
                    owned_qty = existing_pos.qty if existing_pos else 0
                    rejections.append(
                        f"Cannot SELL {proposal.quantity} share(s) of {proposal.symbol}. Currently own {owned_qty} shares."
                    )

        passed = len(rejections) == 0
        if not passed:
            logger.warning("Risk check FAILED for %s: %s", proposal_id, "; ".join(rejections))
        else:
            logger.info("Risk check PASSED for proposal %s", proposal_id)

        result = RiskCheckResult(
            passed=passed,
            proposal_id=proposal_id,
            checks_performed=checks,
            rejection_reasons=rejections,
            evaluated_at=now_str,
        )
        return result, proposal
