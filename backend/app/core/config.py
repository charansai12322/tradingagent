"""Centralized, validated configuration for the AI Trading Agent backend.

Loads environment variables from environment and local .env file using Pydantic Settings.
Fails safely when optional or provider-specific keys are absent.
Strictly prohibits live-trading configuration in this phase.
"""

from functools import lru_cache
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema with built-in validation and security safeguards."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- AI & LLM Configuration ---
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API Key for LLM analysis. Required for AI analysis.",
    )

    # --- Market Data & News Providers ---
    TWELVEDATA_API_KEY: Optional[str] = Field(
        default=None,
        description="TwelveData API Key for stock quotes, historical data, and technical indicators.",
    )
    FINNHUB_API_KEY: Optional[str] = Field(
        default=None,
        description="Finnhub API Key for company news headlines.",
    )

    # --- Broker / Execution Credentials (Paper Trading Only) ---
    ALPACA_API_KEY: Optional[str] = Field(
        default=None,
        description="Alpaca Paper Trading Key ID.",
    )
    ALPACA_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="Alpaca Paper Trading Secret Key.",
    )
    ALPACA_BASE_URL: str = Field(
        default="https://paper-api.alpaca.markets",
        description="Base URL for Alpaca API. Must be paper-api.",
    )

    # --- Telemetry & Observability ---
    LANGSMITH_API_KEY: Optional[str] = Field(
        default=None,
        description="Optional LangSmith API Key for agent tracing.",
    )
    LANGSMITH_TRACING: bool = Field(
        default=False,
        description="Whether to enable LangSmith tracing.",
    )
    LANGSMITH_PROJECT: str = Field(
        default="tradingagent",
        description="LangSmith project name.",
    )
    LANGSMITH_ENDPOINT: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint URL.",
    )

    # --- Application Runtime ---
    APP_ENV: Literal["development", "test", "production"] = Field(
        default="development",
        description="Application environment.",
    )
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Standard logging level.",
    )

    # --- Trading Mode & Strict Execution Controls ---
    TRADING_MODE: Literal["paper"] = Field(
        default="paper",
        description="Trading mode. Only 'paper' is permitted in Phase 2.",
    )
    TRADING_ENABLED: bool = Field(
        default=False,
        description="Global master switch for order execution. Default is false (disabled).",
    )
    ORDER_APPROVAL_REQUIRED: bool = Field(
        default=True,
        description="Whether Human-in-the-Loop order approval is strictly enforced.",
    )

    # --- Quantitative Risk Limits (USD) ---
    MAX_ORDER_NOTIONAL_USD: float = Field(
        default=100.0,
        ge=1.0,
        description="Maximum permissible total value (price * quantity) for a single order.",
    )
    MAX_POSITION_NOTIONAL_USD: float = Field(
        default=500.0,
        ge=1.0,
        description="Maximum permissible total portfolio exposure for any single ticker symbol.",
    )

    @field_validator("TRADING_MODE", mode="before")
    @classmethod
    def validate_trading_mode(cls, v: str) -> str:
        """Strictly prohibit live trading."""
        val = str(v).strip().lower()
        if val != "paper":
            raise ValueError(
                f"TRADING_MODE='{v}' is strictly prohibited. Only 'paper' mode is permitted."
            )
        return "paper"

    @field_validator("ALPACA_BASE_URL")
    @classmethod
    def validate_alpaca_url(cls, v: str) -> str:
        """Ensure Alpaca URL points exclusively to the paper-trading endpoint."""
        val = str(v).strip().rstrip("/")
        if "api.alpaca.markets" in val and "paper-api.alpaca.markets" not in val:
            raise ValueError(
                f"Live Alpaca API endpoint detected ('{v}'). Only 'https://paper-api.alpaca.markets' is permitted."
            )
        return val

    # --- Provider Readiness Helpers ---
    @property
    def has_gemini_key(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip())

    @property
    def has_twelvedata_key(self) -> bool:
        return bool(self.TWELVEDATA_API_KEY and self.TWELVEDATA_API_KEY.strip())

    @property
    def has_finnhub_key(self) -> bool:
        return bool(self.FINNHUB_API_KEY and self.FINNHUB_API_KEY.strip())

    @property
    def has_alpaca_credentials(self) -> bool:
        return bool(
            self.ALPACA_API_KEY
            and self.ALPACA_SECRET_KEY
            and self.ALPACA_API_KEY.strip()
            and self.ALPACA_SECRET_KEY.strip()
        )

    @property
    def has_langsmith_key(self) -> bool:
        return bool(self.LANGSMITH_API_KEY and self.LANGSMITH_API_KEY.strip())

    @property
    def is_langsmith_configured(self) -> bool:
        return bool(
            self.LANGSMITH_TRACING
            and self.LANGSMITH_API_KEY
            and self.LANGSMITH_API_KEY.strip()
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton instance of application settings."""
    return Settings()
