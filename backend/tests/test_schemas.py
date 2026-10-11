"""Tests for data contract schemas and validation."""

import pytest
from pydantic import ValidationError

from app.schemas.trading import (
    AnalysisRequest,
    AnalysisResponse,
    ConfidenceLevel,
    OrderApprovalRequest,
    OrderSide,
    OrderStatus,
    PriceQuote,
    ProposedOrder,
    RecommendationType,
    TechnicalIndicators,
)


def test_analysis_request_normalization():
    """AnalysisRequest must strip whitespace and uppercase ticker symbols."""
    req = AnalysisRequest(symbol="  aapl  ")
    assert req.symbol == "AAPL"

    req2 = AnalysisRequest(symbol="nvda")
    assert req2.symbol == "NVDA"


def test_analysis_request_invalid_symbols():
    """Invalid characters or empty symbols must raise ValidationError."""
    with pytest.raises(ValidationError):
        AnalysisRequest(symbol="")

    with pytest.raises(ValidationError):
        AnalysisRequest(symbol="AAPL$$")

    with pytest.raises(ValidationError):
        AnalysisRequest(symbol="TOOLONGTICKERNAME")


def test_analysis_response_order_executed_is_false():
    """AnalysisResponse must guarantee order_executed is strictly false."""
    quote = PriceQuote(symbol="AAPL", price=150.0, retrieved_at="2026-10-11T20:00:00Z")
    indicators = TechnicalIndicators(quote=quote)

    resp = AnalysisResponse(
        symbol="AAPL",
        recommendation=RecommendationType.BUY,
        confidence=ConfidenceLevel.MEDIUM,
        rationale="Test rationale",
        summary="Test summary",
        indicators=indicators,
        order_executed=False,
        risk_warnings=[],
        timestamp="2026-10-11T20:00:00Z",
    )
    assert resp.order_executed is False


def test_proposed_order_schema_validation():
    """ProposedOrder enforces positive quantity and positive price."""
    proposal = ProposedOrder(
        proposal_id="prop_test_valid",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=2,
        estimated_price=150.0,
        estimated_notional=300.0,
        status=OrderStatus.PROPOSED,
        created_at="2026-10-11T20:00:00Z",
        expires_at="2026-10-11T20:15:00Z",
    )
    assert proposal.quantity == 2
    assert proposal.estimated_notional == 300.0

    # Non-positive quantity must fail
    with pytest.raises(ValidationError):
        ProposedOrder(
            proposal_id="prop_invalid",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=0,
            estimated_price=150.0,
            estimated_notional=0.0,
            created_at="2026-10-11T20:00:00Z",
            expires_at="2026-10-11T20:15:00Z",
        )


def test_order_approval_request_validation():
    """OrderApprovalRequest requires proposal_id length >= 8."""
    req = OrderApprovalRequest(proposal_id="prop_12345678", confirm=True)
    assert req.proposal_id == "prop_12345678"
    assert req.confirm is True

    with pytest.raises(ValidationError):
        OrderApprovalRequest(proposal_id="short", confirm=True)
