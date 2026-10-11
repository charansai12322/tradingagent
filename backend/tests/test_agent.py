"""Tests for AI Trading Agent Service and Gemini output parsing."""

from unittest.mock import AsyncMock, patch
import pytest

from app.core.config import Settings
from app.schemas.trading import (
    ConfidenceLevel,
    NewsArticle,
    OrderSide,
    OrderStatus,
    PriceQuote,
    RecommendationType,
    TechnicalIndicators,
)
from app.services.agent import AgentServiceError, TradingAgentService


@pytest.fixture
def agent_settings():
    return Settings(
        GEMINI_API_KEY="test_gemini_key",
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
    )


@pytest.fixture
def sample_indicators():
    quote = PriceQuote(symbol="NVDA", price=250.0, retrieved_at="2026-10-11T20:00:00Z")
    return TechnicalIndicators(quote=quote)


def test_build_context_prompt_contains_data(agent_settings, sample_indicators):
    """Context prompt must embed price, indicators, and news into template."""
    svc = TradingAgentService(agent_settings)
    news = [NewsArticle(headline="NVDA launches new GPU", source="TechDesk")]
    prompt = svc._build_context_prompt("NVDA", sample_indicators, news)

    assert "NVDA" in prompt
    assert "$250.00" in prompt
    assert "NVDA launches new GPU" in prompt
    assert "recommendation" in prompt


def test_parse_model_output_valid_json(agent_settings):
    """Parses clean markdown JSON blocks into typed AgentAnalysisResult."""
    svc = TradingAgentService(agent_settings)
    raw_llm_json = """```json
    {
      "recommendation": "BUY",
      "confidence": "High",
      "summary": "Strong momentum and bullish moving averages.",
      "rationale": "NVDA maintains clear uptrend support with positive product catalyst.",
      "risk_warnings": ["Volatility risk"]
    }
    ```"""
    parsed = svc._parse_model_output(raw_llm_json)

    assert parsed.recommendation == RecommendationType.BUY
    assert parsed.confidence == ConfidenceLevel.HIGH
    assert "Strong momentum" in parsed.summary
    assert "Volatility risk" in parsed.risk_warnings


def test_parse_model_output_heuristic_fallback(agent_settings):
    """When LLM outputs plain text without JSON, fallback heuristics recover gracefully."""
    svc = TradingAgentService(agent_settings)
    raw_text = "DECISION: BUY\nCONFIDENCE: Medium\nRationale: Stock shows positive momentum."
    parsed = svc._parse_model_output(raw_text)

    assert parsed.recommendation == RecommendationType.BUY
    assert parsed.confidence == ConfidenceLevel.MEDIUM
    assert "fallback" in parsed.risk_warnings[0].lower()


@pytest.mark.asyncio
async def test_analyze_stock_generates_proposal_for_buy(agent_settings, sample_indicators):
    """BUY recommendation must generate a ProposedOrder with unique proposal_id."""
    svc = TradingAgentService(agent_settings)
    mock_response = """```json
    {
      "recommendation": "BUY",
      "confidence": "Medium",
      "summary": "Bullish breakout.",
      "rationale": "High volume price advance.",
      "risk_warnings": []
    }
    ```"""

    with patch.object(svc, "_invoke_gemini", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = mock_response
        analysis, proposal = await svc.analyze_stock("NVDA", sample_indicators, [])

        assert analysis.recommendation == RecommendationType.BUY
        assert proposal is not None
        assert proposal.symbol == "NVDA"
        assert proposal.side == OrderSide.BUY
        assert proposal.quantity == 1
        assert proposal.estimated_price == 250.0
        assert proposal.status == OrderStatus.PROPOSED
        assert proposal.proposal_id.startswith("prop_")


@pytest.mark.asyncio
async def test_analyze_stock_no_proposal_for_hold(agent_settings, sample_indicators):
    """HOLD recommendation must NOT generate an order proposal."""
    svc = TradingAgentService(agent_settings)
    mock_response = """```json
    {
      "recommendation": "HOLD",
      "confidence": "Low",
      "summary": "Neutral market conditions.",
      "rationale": "RSI is balanced, awaiting catalyst.",
      "risk_warnings": []
    }
    ```"""

    with patch.object(svc, "_invoke_gemini", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = mock_response
        analysis, proposal = await svc.analyze_stock("NVDA", sample_indicators, [])

        assert analysis.recommendation == RecommendationType.HOLD
        assert proposal is None


@pytest.mark.asyncio
async def test_analyze_stock_missing_key_raises_error():
    """Attempting model invocation without GEMINI_API_KEY raises AgentServiceError."""
    svc = TradingAgentService(Settings(GEMINI_API_KEY=None, TRADING_MODE="paper"))
    with pytest.raises(AgentServiceError) as exc_info:
        await svc._invoke_gemini("test prompt")
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
