"""Tests for the Guarded Paper Order Execution Service."""

from datetime import datetime, timedelta, timezone
import pytest
import respx
from httpx import Response

from app.core.config import Settings
from app.schemas.trading import (
    OrderApprovalRequest,
    OrderSide,
    OrderStatus,
    ProposedOrder,
)
from app.trading.execution import ExecutionService, ExecutionServiceError
from app.trading.risk import proposal_registry


@pytest.mark.asyncio
async def test_execution_blocked_when_trading_disabled():
    """When TRADING_ENABLED=False, execution service must reject order without calling Alpaca."""
    settings = Settings(
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
    )
    svc = ExecutionService(settings)

    now = datetime.now(timezone.utc)
    proposal = ProposedOrder(
        proposal_id="prop_exec_disabled",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=50.0,
        estimated_notional=50.0,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
    )
    proposal_registry.register(proposal)

    req = OrderApprovalRequest(proposal_id=proposal.proposal_id, confirm=True)

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post("https://paper-api.alpaca.markets/v2/orders")
        result = await svc.execute_approved_proposal(req)

        assert result.success is False
        assert "TRADING_ENABLED is false" in result.message
        # PROOF: Alpaca order endpoint was NEVER called!
        assert route.call_count == 0


@pytest.mark.asyncio
async def test_execution_blocked_when_risk_fails():
    """When risk check fails (e.g. order notional exceeds cap), Alpaca is NEVER called."""
    settings = Settings(
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=True,
        MAX_ORDER_NOTIONAL_USD=100.0,
    )
    svc = ExecutionService(settings)

    now = datetime.now(timezone.utc)
    proposal = ProposedOrder(
        proposal_id="prop_risk_fail",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=300.0,  # Exceeds $100 cap
        estimated_notional=300.0,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
    )
    proposal_registry.register(proposal)

    req = OrderApprovalRequest(proposal_id=proposal.proposal_id, confirm=True)

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post("https://paper-api.alpaca.markets/v2/orders")
        result = await svc.execute_approved_proposal(req)

        assert result.success is False
        assert result.filled_status == "REJECTED_BY_RISK_ENGINE"
        # PROOF: Alpaca endpoint was NEVER called
        assert route.call_count == 0


@pytest.mark.asyncio
async def test_execution_success_with_mocked_alpaca():
    """When risk checks pass and TRADING_ENABLED=True, order is submitted and marked in registry."""
    settings = Settings(
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=True,
        MAX_ORDER_NOTIONAL_USD=100.0,
    )
    svc = ExecutionService(settings)

    now = datetime.now(timezone.utc)
    proposal = ProposedOrder(
        proposal_id="prop_success_order",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=50.0,
        estimated_notional=50.0,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
    )
    proposal_registry.register(proposal)

    req = OrderApprovalRequest(proposal_id=proposal.proposal_id, confirm=True)

    with respx.mock(assert_all_called=True) as respx_mock:
        mock_order_response = {
            "id": "order_mock_alpaca_987",
            "client_order_id": f"agy_{proposal.proposal_id}",
            "symbol": "AAPL",
            "qty": "1",
            "side": "buy",
            "status": "accepted",
        }
        respx_mock.post("https://paper-api.alpaca.markets/v2/orders").mock(
            return_value=Response(200, json=mock_order_response)
        )

        result = await svc.execute_approved_proposal(req)

        assert result.success is True
        assert result.order_id == "order_mock_alpaca_987"
        assert result.client_order_id == f"agy_{proposal.proposal_id}"
        assert result.filled_status == "accepted"
        assert proposal_registry.is_executed(proposal.proposal_id) is True


@pytest.mark.asyncio
async def test_execution_aborts_on_live_base_url():
    """Attempting execution with non-paper URL raises ExecutionServiceError."""
    settings = Settings(
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=True,
    )
    svc = ExecutionService(settings)
    # Manually tamper with base_url to test execution-time guard
    svc.base_url = "https://api.alpaca.markets"

    now = datetime.now(timezone.utc)
    proposal = ProposedOrder(
        proposal_id="prop_live_tamper",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=50.0,
        estimated_notional=50.0,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
    )
    proposal_registry.register(proposal)

    req = OrderApprovalRequest(proposal_id=proposal.proposal_id, confirm=True)
    with pytest.raises(ExecutionServiceError) as exc_info:
        await svc.execute_approved_proposal(req)
    assert "not Alpaca Paper API" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execution_msft_proposal_exceeding_cap_never_calls_alpaca():
    """An MSFT proposal ($535.10) exceeding the $100 cap must be rejected by risk check and NEVER invoke Alpaca."""
    settings = Settings(
        ALPACA_API_KEY="test_key",
        ALPACA_SECRET_KEY="test_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=True,  # Even with execution enabled, risk check blocks submission
        MAX_ORDER_NOTIONAL_USD=100.0,
    )
    svc = ExecutionService(settings)

    now = datetime.now(timezone.utc)
    proposal = ProposedOrder(
        proposal_id="prop_msft_exec_blocked",
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=535.10,
        estimated_notional=535.10,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=(now + timedelta(minutes=15)).isoformat(),
    )
    proposal_registry.register(proposal)

    req = OrderApprovalRequest(proposal_id=proposal.proposal_id, confirm=True)

    with respx.mock(assert_all_called=False) as respx_mock:
        order_route = respx_mock.post("https://paper-api.alpaca.markets/v2/orders")
        result = await svc.execute_approved_proposal(req)

        assert result.success is False
        assert result.filled_status == "REJECTED_BY_RISK_ENGINE"
        assert "Order notional $535.10 exceeds MAX_ORDER_NOTIONAL_USD limit ($100.00)" in result.message
        # MATHEMATICAL PROOF: Alpaca order endpoint was NEVER called!
        assert order_route.call_count == 0

