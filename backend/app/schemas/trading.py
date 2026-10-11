"""Pydantic schemas and contract definitions for AI Trading Agent.

Enforces strict type safety, data validation, and clean boundaries
between analysis recommendations, risk evaluations, and order execution.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class RecommendationType(str, Enum):
    """Trading recommendation types produced by AI analysis."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ConfidenceLevel(str, Enum):
    """Confidence levels associated with agent recommendations."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class OrderSide(str, Enum):
    """Permissible sides for trading orders."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Lifecycle status of a proposed order."""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


# --- Health & Diagnostic Schemas ---

class ProviderStatus(BaseModel):
    """Readiness status for external service integrations."""
    gemini: bool
    twelvedata: bool
    finnhub: bool
    alpaca: bool
    langsmith: bool = False


class HealthResponse(BaseModel):
    """Health check response schema. Requires no credentials to generate."""
    status: str = Field(default="ok", description="Service status")
    app_env: str = Field(description="Environment: development, test, production")
    trading_mode: str = Field(description="Must be 'paper'")
    trading_enabled: bool = Field(description="Order execution kill-switch status")
    order_approval_required: bool = Field(description="Human-in-the-loop requirement status")
    providers: ProviderStatus = Field(description="Configured provider keys")
    timestamp: str = Field(description="ISO-8601 server timestamp")


# --- Market Data & Indicator Schemas ---

class PriceQuote(BaseModel):
    """Latest market price quote for a symbol."""
    symbol: str
    price: float = Field(gt=0, description="Latest price in USD")
    retrieved_at: str


class PriceHistoryItem(BaseModel):
    """Single date closing price."""
    date: str
    close: float = Field(gt=0)


class RsiIndicator(BaseModel):
    """RSI calculation output."""
    time_period: int = 14
    value: float = Field(ge=0, le=100)
    interpretation: str = Field(description="Overbought, Oversold, or Neutral")


class SmaIndicator(BaseModel):
    """Simple Moving Average data and trend evaluation."""
    sma_50: float = Field(gt=0, description="50-day Simple Moving Average")
    sma_200: float = Field(gt=0, description="200-day Simple Moving Average")
    fast_above_slow: bool = Field(description="True if SMA-50 > SMA-200")
    trend_regime: str = Field(description="Bullish uptrend alignment vs Bearish downtrend alignment")
    is_true_crossover: bool = Field(
        default=False,
        description="True only if a Golden/Death cross occurred recently",
    )


class TechnicalIndicators(BaseModel):
    """Combined technical indicator package for a stock."""
    quote: PriceQuote
    history: List[PriceHistoryItem] = Field(default_factory=list)
    rsi: Optional[RsiIndicator] = None
    sma: Optional[SmaIndicator] = None


# --- News Schemas ---

class NewsArticle(BaseModel):
    """Structured company news headline."""
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    datetime: Optional[int] = None
    category: Optional[str] = None


# --- Order Proposal & Approval Contracts ---

class ProposedOrder(BaseModel):
    """Server-side generated order proposal awaiting explicit user confirmation."""
    proposal_id: str = Field(description="Unique server-generated identifier for this proposal")
    symbol: str = Field(description="Stock ticker symbol")
    side: OrderSide = Field(description="Buy or Sell")
    quantity: int = Field(default=1, gt=0, description="Number of shares proposed")
    estimated_price: float = Field(gt=0, description="Latest price estimate at proposal creation")
    estimated_notional: float = Field(gt=0, description="Total estimated order value in USD")
    status: OrderStatus = Field(default=OrderStatus.PROPOSED)
    created_at: str = Field(description="ISO-8601 timestamp of proposal creation")
    expires_at: str = Field(description="ISO-8601 timestamp after which proposal cannot be approved")


class OrderApprovalRequest(BaseModel):
    """Client request to approve and execute a specific proposed order."""
    proposal_id: str = Field(min_length=8, description="Target proposal ID to approve")
    confirm: bool = Field(default=True, description="Explicit human confirmation flag")


class RiskCheckResult(BaseModel):
    """Deterministic result of the pre-trade risk evaluation."""
    passed: bool
    proposal_id: str
    checks_performed: List[str]
    rejection_reasons: List[str] = Field(default_factory=list)
    evaluated_at: str


class OrderExecutionResult(BaseModel):
    """Output from the paper order execution service."""
    success: bool
    proposal_id: str
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    symbol: str
    side: str
    quantity: int
    filled_status: str
    executed_at: str
    message: str


# --- Analysis Request & Response Contracts ---

class AnalysisRequest(BaseModel):
    """Request payload to initiate AI stock analysis."""
    symbol: str = Field(
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z0-9\.\-]+$",
        description="Ticker symbol to analyze, e.g. AAPL, NVDA, MSFT",
    )

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class AnalysisResponse(BaseModel):
    """Complete, validated analysis response returned by the backend.
    
    Guarantees that analysis NEVER executes a trade directly: order_executed is always false.
    """
    symbol: str
    recommendation: RecommendationType
    confidence: ConfidenceLevel
    rationale: str = Field(description="AI explanation synthesized from technicals and news")
    summary: str = Field(description="Executive summary of the stock status")
    indicators: TechnicalIndicators
    news: List[NewsArticle] = Field(default_factory=list)
    proposed_order: Optional[ProposedOrder] = Field(
        default=None,
        description="Generated order proposal if BUY or SELL recommendation was reached; requires approval",
    )
    order_executed: bool = Field(
        default=False,
        description="Always false for analysis responses. Orders require explicit approval.",
    )
    risk_warnings: List[str] = Field(default_factory=list)
    timestamp: str


# --- Portfolio Contracts ---

class PortfolioPosition(BaseModel):
    """Sanitized portfolio position entry."""
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pl: Optional[float] = None
    unrealized_plpc: Optional[float] = None


class PortfolioResponse(BaseModel):
    """Sanitized Alpaca Paper portfolio response."""
    account_status: str
    currency: str = "USD"
    cash: float
    portfolio_value: float
    buying_power: float
    positions: List[PortfolioPosition] = Field(default_factory=list)
    timestamp: str


# --- API Error Contract ---

class ApiErrorResponse(BaseModel):
    """Standardized error response payload."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str
