"""FastAPI Application Entry Point for AI Trading Agent.

Initializes the API server, configures CORS middleware, sets up logging,
and mounts API routes. Makes zero external network requests on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging_config import setup_logging

# Load centralized settings and configure logging
settings = get_settings()
logger = setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler. Configures diagnostics and LangSmith safely on startup."""
    logger.info("=" * 60)
    logger.info("AI Trading Agent API initialized successfully.")
    logger.info("Environment: %s | Log Level: %s", settings.APP_ENV, settings.LOG_LEVEL)
    logger.info("Trading Mode: %s | Trading Enabled: %s", settings.TRADING_MODE, settings.TRADING_ENABLED)
    logger.info("Order Approval Required: %s", settings.ORDER_APPROVAL_REQUIRED)
    logger.info("Alpaca Endpoint: %s", settings.ALPACA_BASE_URL)
    logger.info("CORS Allowed Origins: %s", settings.CORS_ORIGINS)
    if settings.is_langsmith_configured:
        import os
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        logger.info("LangSmith Tracing: ENABLED (Project: %s)", settings.LANGSMITH_PROJECT)
    else:
        import os
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.info("LangSmith Tracing: DISABLED")
    logger.info("=" * 60)
    yield


# Initialize FastAPI application
app = FastAPI(
    title="AI Trading Agent API",
    description=(
        "Production-style backend for the AI Trading Agent. "
        "Integrates TwelveData market data, Finnhub news, Google Gemini 2.5 Flash analysis, "
        "and Alpaca paper trading with a deterministic risk gateway and Human-in-the-Loop order approval."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)
