"""Tests for Alpaca Paper Portfolio Service."""

import pytest
import respx
from httpx import Response

from app.core.config import Settings
from app.services.portfolio import PortfolioService, PortfolioServiceError


@pytest.fixture
def portfolio_settings():
    return Settings(
        ALPACA_API_KEY="test_alpaca_key",
        ALPACA_SECRET_KEY="test_alpaca_secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
    )


@pytest.mark.asyncio
async def test_get_portfolio_success(portfolio_settings):
    """Account balance and active equity positions parsed correctly."""
    svc = PortfolioService(portfolio_settings)

    mock_account = {
        "status": "ACTIVE",
        "currency": "USD",
        "cash": "25000.50",
        "portfolio_value": "35000.75",
        "buying_power": "100000.00",
    }
    mock_positions = [
        {
            "symbol": "AAPL",
            "qty": "5",
            "avg_entry_price": "150.00",
            "current_price": "155.00",
            "market_value": "775.00",
            "unrealized_pl": "25.00",
            "unrealized_plpc": "0.0333",
        }
    ]

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get("https://paper-api.alpaca.markets/v2/account").mock(
            return_value=Response(200, json=mock_account)
        )
        respx_mock.get("https://paper-api.alpaca.markets/v2/positions").mock(
            return_value=Response(200, json=mock_positions)
        )

        resp = await svc.get_portfolio()
        assert resp.account_status == "ACTIVE"
        assert resp.cash == 25000.50
        assert resp.portfolio_value == 35000.75
        assert len(resp.positions) == 1
        assert resp.positions[0].symbol == "AAPL"
        assert resp.positions[0].qty == 5.0
        assert resp.positions[0].market_value == 775.00


@pytest.mark.asyncio
async def test_portfolio_missing_credentials():
    """Missing Alpaca credentials raises PortfolioServiceError."""
    svc = PortfolioService(
        Settings(
            ALPACA_API_KEY=None,
            ALPACA_SECRET_KEY=None,
            ALPACA_BASE_URL="https://paper-api.alpaca.markets",
            TRADING_MODE="paper",
        )
    )
    with pytest.raises(PortfolioServiceError) as exc_info:
        await svc.get_portfolio()
    assert "missing" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_portfolio_unauthorized_credentials(portfolio_settings):
    """HTTP 401/403 status from Alpaca returns clean error message."""
    svc = PortfolioService(portfolio_settings)

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get("https://paper-api.alpaca.markets/v2/account").mock(
            return_value=Response(401, text="Unauthorized")
        )
        with pytest.raises(PortfolioServiceError) as exc_info:
            await svc.get_portfolio()
        assert "Invalid Alpaca credentials" in str(exc_info.value)


def test_portfolio_live_url_rejected():
    """Instantiation with live Alpaca URL is blocked by safety guard."""
    live_settings = Settings(
        ALPACA_API_KEY="key",
        ALPACA_SECRET_KEY="secret",
        ALPACA_BASE_URL="https://paper-api.alpaca.markets",
        TRADING_MODE="paper",
    )
    live_settings.ALPACA_BASE_URL = "https://api.alpaca.markets"
    with pytest.raises(PortfolioServiceError) as exc_info:
        PortfolioService(live_settings)
    assert "Insecure base URL" in str(exc_info.value)
