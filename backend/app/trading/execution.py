"""Guarded Paper Order Execution Service.

Communicates with Alpaca Paper Trading REST API to submit market orders.
Mandatory safeguards:
- Revalidates risk checks immediately prior to submission.
- Blocks execution if TRADING_ENABLED=false.
- Rejects any live endpoint configuration.
- Enforces idempotency via proposal-bound client_order_id.
- Reports failure safely without leaking sensitive account headers.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
import httpx

from app.core.config import Settings, get_settings
from app.schemas.trading import (
    OrderApprovalRequest,
    OrderExecutionResult,
    PortfolioResponse,
    ProposedOrder,
)
from app.trading.risk import RiskEngine, proposal_registry

logger = logging.getLogger("tradingagent.execution")


class ExecutionServiceError(Exception):
    """Raised when order submission fails."""
    pass


class ExecutionService:
    """Service handling verified paper order routing."""

    def __init__(self, settings: Optional[Settings] = None, risk_engine: Optional[RiskEngine] = None):
        self.settings = settings or get_settings()
        self.risk_engine = risk_engine or RiskEngine(self.settings)
        self.base_url = self.settings.ALPACA_BASE_URL.rstrip("/")
        self.api_key = self.settings.ALPACA_API_KEY
        self.secret_key = self.settings.ALPACA_SECRET_KEY
        self.timeout = 10.0

    def _get_headers(self) -> dict:
        """Construct secure Alpaca paper authentication headers."""
        if not self.api_key or not self.secret_key:
            raise ExecutionServiceError(
                "ALPACA_API_KEY or ALPACA_SECRET_KEY is not configured in backend environment."
            )
        return {
            "APCA-API-KEY-ID": self.api_key.strip(),
            "APCA-API-SECRET-KEY": self.secret_key.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def execute_approved_proposal(
        self,
        approval_req: OrderApprovalRequest,
        portfolio: Optional[PortfolioResponse] = None,
    ) -> OrderExecutionResult:
        """Execute a proposal following strict risk validation."""
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Evaluate Pre-Trade Risk
        risk_result, proposal = self.risk_engine.evaluate_approval(approval_req, portfolio)
        if not risk_result.passed or not proposal:
            reasons = "; ".join(risk_result.rejection_reasons)
            logger.warning("Order execution REJECTED: %s", reasons)
            return OrderExecutionResult(
                success=False,
                proposal_id=approval_req.proposal_id,
                order_id=None,
                client_order_id=None,
                symbol=proposal.symbol if proposal else "UNKNOWN",
                side=proposal.side.value if proposal else "UNKNOWN",
                quantity=proposal.quantity if proposal else 0,
                filled_status="REJECTED_BY_RISK_ENGINE",
                executed_at=now_str,
                message=f"Pre-trade risk checks failed: {reasons}",
            )

        # 2. Re-verify configuration and paper URL
        if not self.settings.TRADING_ENABLED:
            return OrderExecutionResult(
                success=False,
                proposal_id=proposal.proposal_id,
                symbol=proposal.symbol,
                side=proposal.side.value,
                quantity=proposal.quantity,
                filled_status="DISABLED",
                executed_at=now_str,
                message="TRADING_ENABLED is false. Execution aborted.",
            )

        if "paper-api.alpaca.markets" not in self.base_url:
            raise ExecutionServiceError(
                f"Aborting execution: Base URL '{self.base_url}' is not Alpaca Paper API."
            )

        # 3. Construct Order Payload
        client_order_id = f"agy_{proposal.proposal_id}"
        payload = {
            "symbol": proposal.symbol.upper(),
            "qty": str(proposal.quantity),
            "side": proposal.side.value.lower(),
            "type": "market",
            "time_in_force": "day",
            "client_order_id": client_order_id,
        }

        # 4. Submit Order to Alpaca Paper Trading
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v2/orders",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            error_body = exc.response.text
            logger.error("Alpaca order submission failed HTTP %s: %s", exc.response.status_code, error_body)
            return OrderExecutionResult(
                success=False,
                proposal_id=proposal.proposal_id,
                symbol=proposal.symbol,
                side=proposal.side.value,
                quantity=proposal.quantity,
                filled_status="PROVIDER_REJECTED",
                executed_at=now_str,
                message=f"Alpaca rejected order (HTTP {exc.response.status_code}): {error_body[:200]}",
            )
        except httpx.HTTPError as exc:
            logger.error("Alpaca network connection error: %s", exc)
            return OrderExecutionResult(
                success=False,
                proposal_id=proposal.proposal_id,
                symbol=proposal.symbol,
                side=proposal.side.value,
                quantity=proposal.quantity,
                filled_status="NETWORK_ERROR",
                executed_at=now_str,
                message=f"Network error communicating with Alpaca: {str(exc)}",
            )

        # 5. Mark Proposal as Executed in Registry
        proposal_registry.mark_executed(proposal.proposal_id)
        order_id = data.get("id")
        status = data.get("status", "submitted")

        logger.info(
            "Order successfully placed on Alpaca Paper: OrderID=%s, Symbol=%s, Side=%s, Qty=%s",
            order_id,
            proposal.symbol,
            proposal.side.value,
            proposal.quantity,
        )

        return OrderExecutionResult(
            success=True,
            proposal_id=proposal.proposal_id,
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=proposal.symbol,
            side=proposal.side.value,
            quantity=proposal.quantity,
            filled_status=status,
            executed_at=now_str,
            message=f"Paper trade order submitted successfully. Status: {status}",
        )
