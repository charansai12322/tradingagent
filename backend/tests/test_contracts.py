"""Tests verifying that backend Pydantic contracts match frontend TypeScript expectations."""

from datetime import datetime, timezone
from app.schemas.trading import (
    AnalysisRequest,
    AnalysisResponse,
    ConfidenceLevel,
    HealthResponse,
    NewsArticle,
    OrderApprovalRequest,
    OrderExecutionResult,
    OrderSide,
    OrderStatus,
    PortfolioPosition,
    PortfolioResponse,
    PriceHistoryItem,
    PriceQuote,
    ProposedOrder,
    ProviderStatus,
    RecommendationType,
    RiskCheckResult,
    RsiIndicator,
    SmaIndicator,
    TechnicalIndicators,
)


def test_recommendation_enum_contract():
    """Enum values must strictly match TypeScript RecommendationType ('BUY' | 'SELL' | 'HOLD')."""
    assert [e.value for e in RecommendationType] == ["BUY", "SELL", "HOLD"]


def test_confidence_enum_contract():
    """Enum values must strictly match TypeScript ConfidenceLevel ('High' | 'Medium' | 'Low')."""
    assert [e.value for e in ConfidenceLevel] == ["High", "Medium", "Low"]


def test_order_side_enum_contract():
    """Enum values must strictly match TypeScript OrderSide ('buy' | 'sell')."""
    assert [e.value for e in OrderSide] == ["buy", "sell"]


def test_order_status_enum_contract():
    """Enum values must match TypeScript OrderStatus ('PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'EXPIRED')."""
    assert [e.value for e in OrderStatus] == ["PROPOSED", "APPROVED", "REJECTED", "EXECUTED", "EXPIRED"]


def test_analysis_response_json_serialization():
    """Serialized JSON fields of AnalysisResponse must match frontend TypeScript contract exactly."""
    now_str = datetime.now(timezone.utc).isoformat()
    quote = PriceQuote(symbol="AAPL", price=150.0, retrieved_at=now_str)
    indicators = TechnicalIndicators(
        quote=quote,
        history=[PriceHistoryItem(date="2026-10-08", close=150.0)],
        rsi=RsiIndicator(time_period=14, value=50.0, interpretation="Neutral"),
        sma=SmaIndicator(
            sma_50=145.0,
            sma_200=140.0,
            fast_above_slow=True,
            trend_regime="Bullish",
            is_true_crossover=False,
        ),
    )
    news = [NewsArticle(headline="Test headline", source="Reuters")]
    proposal = ProposedOrder(
        proposal_id="prop_contract_test",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=1,
        estimated_price=150.0,
        estimated_notional=150.0,
        status=OrderStatus.PROPOSED,
        created_at=now_str,
        expires_at=now_str,
    )

    resp = AnalysisResponse(
        symbol="AAPL",
        recommendation=RecommendationType.BUY,
        confidence=ConfidenceLevel.HIGH,
        rationale="Strong indicators",
        summary="Positive outlook",
        indicators=indicators,
        news=news,
        proposed_order=proposal,
        order_executed=False,
        risk_warnings=["Advisory only"],
        timestamp=now_str,
    )

    data = resp.model_dump()
    expected_keys = {
        "symbol",
        "recommendation",
        "confidence",
        "rationale",
        "summary",
        "indicators",
        "news",
        "proposed_order",
        "order_executed",
        "risk_warnings",
        "timestamp",
    }
    assert set(data.keys()) == expected_keys
    assert data["order_executed"] is False
    assert data["proposed_order"]["proposal_id"] == "prop_contract_test"


def test_health_response_json_serialization():
    """Serialized JSON of HealthResponse must match frontend expectations."""
    now_str = datetime.now(timezone.utc).isoformat()
    health = HealthResponse(
        status="ok",
        app_env="test",
        trading_mode="paper",
        trading_enabled=False,
        order_approval_required=True,
        providers=ProviderStatus(
            gemini=True,
            twelvedata=True,
            finnhub=True,
            alpaca=True,
            langsmith=False,
        ),
        timestamp=now_str,
    )
    data = health.model_dump()
    assert "status" in data
    assert "providers" in data
    assert "langsmith" in data["providers"]
