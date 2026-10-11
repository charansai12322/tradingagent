"""End-to-end API integration tests using FastAPI TestClient."""

from unittest.mock import AsyncMock, patch
import pytest

from app.schemas.trading import (
    ConfidenceLevel,
    PriceQuote,
    RecommendationType,
    TechnicalIndicators,
)
from app.services.agent import AgentAnalysisResult, AgentServiceError
from app.services.market_data import MarketDataError
from app.services.portfolio import PortfolioServiceError


def test_unknown_route_returns_404(client):
    """Unknown API routes must return HTTP 404."""
    response = client.get("/api/v1/nonexistent_route")
    assert response.status_code == 404


def test_analyze_invalid_symbol_returns_422(client):
    """Malformed request payload or invalid ticker characters must return HTTP 422."""
    response = client.post("/api/v1/analyze", json={"symbol": "$$INVALID%%"})
    assert response.status_code == 422


def test_analyze_end_to_end_flow(client):
    """POST /api/v1/analyze returns complete analysis and proposal with order_executed=False."""
    mock_quote = PriceQuote(symbol="MSFT", price=320.0, retrieved_at="2026-10-11T20:00:00Z")
    mock_indicators = TechnicalIndicators(quote=mock_quote)

    mock_analysis_result = AgentAnalysisResult(
        recommendation=RecommendationType.BUY,
        confidence=ConfidenceLevel.HIGH,
        summary="Constructive momentum.",
        rationale="Clear technical support above moving averages.",
        risk_warnings=[],
    )

    with patch("app.api.routes.MarketDataService.get_technical_indicators", new_callable=AsyncMock) as mock_md, \
         patch("app.api.routes.NewsService.get_company_news", new_callable=AsyncMock) as mock_news, \
         patch("app.api.routes.TradingAgentService.analyze_stock", new_callable=AsyncMock) as mock_agent:

        mock_md.return_value = mock_indicators
        mock_news.return_value = []
        mock_agent.return_value = (mock_analysis_result, None)

        response = client.post("/api/v1/analyze", json={"symbol": "msft"})
        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "MSFT"
        assert data["recommendation"] == "BUY"
        assert data["confidence"] == "High"
        assert data["order_executed"] is False
        assert data["indicators"]["quote"]["price"] == 320.0


def test_analyze_market_data_error_returns_502(client):
    """When market data provider fails, return controlled HTTP 502 Bad Gateway."""
    with patch("app.api.routes.MarketDataService.get_technical_indicators", new_callable=AsyncMock) as mock_md:
        mock_md.side_effect = MarketDataError("TwelveData quota exceeded")

        response = client.post("/api/v1/analyze", json={"symbol": "NVDA"})
        assert response.status_code == 502
        assert "Market data provider error" in response.json()["detail"]


def test_analyze_agent_error_returns_502(client):
    """When AI agent synthesis fails, return controlled HTTP 502 Bad Gateway."""
    mock_quote = PriceQuote(symbol="NVDA", price=250.0, retrieved_at="2026-10-11T20:00:00Z")
    mock_indicators = TechnicalIndicators(quote=mock_quote)

    with patch("app.api.routes.MarketDataService.get_technical_indicators", new_callable=AsyncMock) as mock_md, \
         patch("app.api.routes.NewsService.get_company_news", new_callable=AsyncMock) as mock_news, \
         patch("app.api.routes.TradingAgentService.analyze_stock", new_callable=AsyncMock) as mock_agent:

        mock_md.return_value = mock_indicators
        mock_news.return_value = []
        mock_agent.side_effect = AgentServiceError("Gemini rate limit")

        response = client.post("/api/v1/analyze", json={"symbol": "NVDA"})
        assert response.status_code == 502
        assert "AI Agent analysis failed" in response.json()["detail"]


def test_portfolio_error_returns_502(client):
    """When Alpaca portfolio fails, return controlled HTTP 502 Bad Gateway."""
    with patch("app.api.routes.PortfolioService.get_portfolio", new_callable=AsyncMock) as mock_port:
        mock_port.side_effect = PortfolioServiceError("Alpaca service unavailable")

        response = client.get("/api/v1/portfolio")
        assert response.status_code == 502
        assert "Failed to retrieve portfolio data" in response.json()["detail"]


def test_orders_approve_when_disabled(client, sample_proposal):
    """Approving an order when TRADING_ENABLED=False must return success=False safely."""
    response = client.post(
        "/api/v1/orders/approve",
        json={"proposal_id": sample_proposal.proposal_id, "confirm": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "TRADING_ENABLED is false" in data["message"]


def test_orders_approve_missing_proposal(client):
    """Approving an unknown proposal must return success=False with rejection notice."""
    response = client.post(
        "/api/v1/orders/approve",
        json={"proposal_id": "prop_nonexistent_999", "confirm": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["message"].lower()
