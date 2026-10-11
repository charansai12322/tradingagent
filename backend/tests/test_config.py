"""Tests for centralized configuration and logging security."""

import logging
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.logging_config import SensitiveDataFilter, setup_logging


def test_default_config_safe_values():
    """Settings must apply secure defaults prohibiting execution."""
    s = Settings(
        GEMINI_API_KEY=None,
        TWELVEDATA_API_KEY=None,
        FINNHUB_API_KEY=None,
        ALPACA_API_KEY=None,
        ALPACA_SECRET_KEY=None,
    )
    assert s.TRADING_MODE == "paper"
    assert s.TRADING_ENABLED is False
    assert s.ORDER_APPROVAL_REQUIRED is True
    assert s.MAX_ORDER_NOTIONAL_USD == 100.0
    assert s.MAX_POSITION_NOTIONAL_USD == 500.0
    assert s.ALPACA_BASE_URL == "https://paper-api.alpaca.markets"
    assert s.LANGSMITH_TRACING is False
    assert s.LANGSMITH_ENDPOINT == "https://api.smith.langchain.com"
    assert s.is_langsmith_configured is False


def test_prohibit_live_trading_mode():
    """Attempting to configure TRADING_MODE='live' must raise a ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(TRADING_MODE="live")
    assert "strictly prohibited" in str(exc_info.value).lower()


def test_prohibit_live_alpaca_url():
    """Configuring a live Alpaca broker URL must be rejected by validator."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(ALPACA_BASE_URL="https://api.alpaca.markets")
    assert "live alpaca api endpoint detected" in str(exc_info.value).lower()


def test_langsmith_configuration_toggles():
    """LangSmith is only configured if both TRACING is true and key is provided."""
    s1 = Settings(LANGSMITH_API_KEY="key123", LANGSMITH_TRACING=False)
    assert s1.has_langsmith_key is True
    assert s1.is_langsmith_configured is False

    s2 = Settings(LANGSMITH_API_KEY="key123", LANGSMITH_TRACING=True)
    assert s2.is_langsmith_configured is True

    s3 = Settings(LANGSMITH_API_KEY=None, LANGSMITH_TRACING=True)
    assert s3.is_langsmith_configured is False


def test_sensitive_data_logging_filter():
    """SensitiveDataFilter must redact sensitive authorization keywords."""
    f = SensitiveDataFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Error connecting with apikey=12345 secret=abcde",
        args=(),
        exc_info=None,
    )
    f.filter(record)
    assert record.msg == "[REDACTED_SENSITIVE_DATA_IN_LOG]"


def test_settings_singleton_caching():
    """get_settings returns identical cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
