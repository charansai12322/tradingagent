"""FastAPI API routes for AI Trading Agent backend.

Endpoints:
- GET  /health              : Instant system diagnostic, requires zero keys or network calls.
- POST /api/v1/analyze      : Market data + indicators + news + Gemini analysis. Never executes trades.
- GET  /api/v1/portfolio    : Read-only Alpaca Paper balance and positions.
- POST /api/v1/orders/approve: Validates risk constraints and executes paper trade only upon explicit consent.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.trading import (
    AnalysisRequest,
    AnalysisResponse,
    HealthResponse,
    OrderApprovalRequest,
    OrderExecutionResult,
    PortfolioResponse,
    ProviderStatus,
)
from app.services.agent import AgentServiceError, TradingAgentService
from app.services.market_data import MarketDataError, MarketDataService
from app.services.news import NewsService
from app.services.portfolio import PortfolioService, PortfolioServiceError
from app.trading.execution import ExecutionService
from app.trading.risk import RiskEngine, proposal_registry

logger = logging.getLogger("tradingagent.api")
router = APIRouter()


# --- Dependencies ---

def get_market_service(settings: Settings = Depends(get_settings)) -> MarketDataService:
    return MarketDataService(settings)


def get_news_service(settings: Settings = Depends(get_settings)) -> NewsService:
    return NewsService(settings)


def get_portfolio_service(settings: Settings = Depends(get_settings)) -> PortfolioService:
    return PortfolioService(settings)


def get_agent_service(settings: Settings = Depends(get_settings)) -> TradingAgentService:
    return TradingAgentService(settings)


def get_execution_service(settings: Settings = Depends(get_settings)) -> ExecutionService:
    return ExecutionService(settings)


# --- Endpoints ---

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health & Provider Diagnostics",
    tags=["Diagnostics"],
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Instant health check. Requires zero credentials and makes zero external requests."""
    providers = ProviderStatus(
        gemini=settings.has_gemini_key,
        twelvedata=settings.has_twelvedata_key,
        finnhub=settings.has_finnhub_key,
        alpaca=settings.has_alpaca_credentials,
        langsmith=settings.is_langsmith_configured,
    )
    return HealthResponse(
        status="ok",
        app_env=settings.APP_ENV,
        trading_mode=settings.TRADING_MODE,
        trading_enabled=settings.TRADING_ENABLED,
        order_approval_required=settings.ORDER_APPROVAL_REQUIRED,
        providers=providers,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/api/v1/analyze",
    response_model=AnalysisResponse,
    summary="Analyze Stock with Technical Indicators & AI Agent",
    tags=["Analysis"],
)
async def analyze_stock(
    request: AnalysisRequest,
    market_svc: MarketDataService = Depends(get_market_service),
    news_svc: NewsService = Depends(get_news_service),
    agent_svc: TradingAgentService = Depends(get_agent_service),
) -> AnalysisResponse:
    """Analyze stock symbol using market data, indicators, and AI synthesis.
    
    GUARANTEE: This endpoint NEVER executes orders. order_executed is always false.
    If recommendation is BUY or SELL, a ProposedOrder with unique proposal_id is generated
    and requires explicit call to /api/v1/orders/approve to execute.
    """
    symbol = request.symbol
    logger.info("Starting analysis for symbol: %s", symbol)

    # 1. Fetch Technical Indicators from TwelveData
    try:
        indicators = await market_svc.get_technical_indicators(symbol)
    except MarketDataError as exc:
        logger.error("Market data failure for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Market data provider error for '{symbol}': {str(exc)}",
        )

    # 2. Fetch News from Finnhub (treated as untrusted external text)
    news = await news_svc.get_company_news(symbol, lookback_days=7, max_articles=5)

    # 3. Perform AI Synthesis via Gemini 2.5 Flash
    try:
        parsed_analysis, proposed_order = await agent_svc.analyze_stock(symbol, indicators, news)
    except AgentServiceError as exc:
        logger.error("AI Agent failure for %s: %s", symbol, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI Agent analysis failed for '{symbol}': {str(exc)}",
        )

    # 4. Register Proposed Order in Memory Store if created
    if proposed_order:
        proposal_registry.register(proposed_order)

    return AnalysisResponse(
        symbol=symbol,
        recommendation=parsed_analysis.recommendation,
        confidence=parsed_analysis.confidence,
        rationale=parsed_analysis.rationale,
        summary=parsed_analysis.summary,
        indicators=indicators,
        news=news,
        proposed_order=proposed_order,
        order_executed=False,  # Explicitly false: analysis never trades directly
        risk_warnings=parsed_analysis.risk_warnings,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/api/v1/portfolio",
    response_model=PortfolioResponse,
    summary="Get Alpaca Paper Account & Positions",
    tags=["Portfolio"],
)
async def get_portfolio(
    portfolio_svc: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioResponse:
    """Fetch virtual cash balance, buying power, and active paper positions."""
    try:
        return await portfolio_svc.get_portfolio()
    except PortfolioServiceError as exc:
        logger.error("Portfolio retrieval error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to retrieve portfolio data: {str(exc)}",
        )


@router.post(
    "/api/v1/orders/approve",
    response_model=OrderExecutionResult,
    summary="Approve and Execute a Proposed Order",
    tags=["Execution"],
)
async def approve_order(
    request: OrderApprovalRequest,
    execution_svc: ExecutionService = Depends(get_execution_service),
    portfolio_svc: PortfolioService = Depends(get_portfolio_service),
) -> OrderExecutionResult:
    """Human-in-the-Loop order approval gateway.
    
    Validates explicit consent, checks pre-trade risk controls, verifies proposal status,
    and submits paper trade order to Alpaca if and only if all checks pass and TRADING_ENABLED=true.
    """
    logger.info("Order approval received for proposal_id: %s", request.proposal_id)

    # Attempt to fetch active portfolio for real-time risk checks (e.g. position sizing, owned shares)
    portfolio: Optional[PortfolioResponse] = None
    try:
        portfolio = await portfolio_svc.get_portfolio()
    except Exception as exc:
        logger.warning("Could not fetch real-time portfolio during approval risk check: %s", exc)

    # Execute order through risk gate
    result = await execution_svc.execute_approved_proposal(request, portfolio)
    return result
