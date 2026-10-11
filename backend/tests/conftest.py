"""Pytest fixtures and configuration for AI Trading Agent test suite.

Mocks all external network providers to guarantee deterministic, air-gapped testing.
Resets in-memory state and proposal registries between tests.
"""

from datetime import datetime, timedelta, timezone
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is in sys.path
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.trading import (
    OrderSide,
    OrderStatus,
    PortfolioPosition,
    PortfolioResponse,
    ProposedOrder,
)
from app.trading.risk import proposal_registry


@pytest.fixture(autouse=True)
def reset_proposal_registry():
    """Ensure in-memory proposal registry is cleared before and after every test."""
    proposal_registry._proposals.clear()
    proposal_registry._executed_ids.clear()
    yield
    proposal_registry._proposals.clear()
    proposal_registry._executed_ids.clear()


@pytest.fixture
def mock_settings():
    """Deterministic test settings with paper mode and disabled execution."""
    return Settings(
        GEMINI_API_KEY="test_gemini_key_12345",
        TWELVEDATA_API_KEY="test_twelvedata_key_12345",
        FINNHUB_API_KEY="test_finnhub_key_12345",
        ALPACA_API_KEY="test_alpaca_key_12345",
        ALPACA_SECRET_KEY="test_alpaca_secret_12345",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        LANGSMITH_API_KEY="test_langsmith_key_12345",
        LANGSMITH_TRACING=False,
        LANGSMITH_PROJECT="tradingagent_test",
        APP_ENV="test",
        LOG_LEVEL="INFO",
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
        ORDER_APPROVAL_REQUIRED=True,
        MAX_ORDER_NOTIONAL_USD=100.0,
        MAX_POSITION_NOTIONAL_USD=500.0,
    )


@pytest.fixture
def client(mock_settings):
    """FastAPI TestClient with overridden settings dependency."""
    app.dependency_overrides[get_settings] = lambda: mock_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_proposal():
    """Create and register a valid, unexpired order proposal."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=15)
    proposal = ProposedOrder(
        proposal_id="prop_test_12345678",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=50.0,
        estimated_notional=50.0,
        status=OrderStatus.PROPOSED,
        created_at=now.isoformat(),
        expires_at=expires.isoformat(),
    )
    proposal_registry.register(proposal)
    return proposal


@pytest.fixture
def sample_portfolio():
    """Sample paper portfolio response for risk checks."""
    return PortfolioResponse(
        account_status="ACTIVE",
        currency="USD",
        cash=10000.0,
        portfolio_value=15000.0,
        buying_power=40000.0,
        positions=[
            PortfolioPosition(
                symbol="AAPL",
                qty=10.0,
                avg_entry_price=150.0,
                current_price=155.0,
                market_value=1550.0,
                unrealized_pl=50.0,
                unrealized_plpc=0.033,
            ),
            PortfolioPosition(
                symbol="MSFT",
                qty=5.0,
                avg_entry_price=300.0,
                current_price=310.0,
                market_value=1550.0,
                unrealized_pl=50.0,
                unrealized_plpc=0.033,
            ),
        ],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
