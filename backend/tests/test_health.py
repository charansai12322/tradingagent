"""Tests for system health check and diagnostics endpoint."""

from app.core.config import Settings, get_settings
from app.main import app


def test_health_endpoint_success(client, mock_settings):
    """GET /health must return HTTP 200 with accurate diagnostic flags and zero secret leakage."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["app_env"] == "test"
    assert data["trading_mode"] == "paper"
    assert data["trading_enabled"] is False
    assert data["order_approval_required"] is True
    assert "timestamp" in data

    # Verify provider flags
    providers = data["providers"]
    assert providers["gemini"] is True
    assert providers["twelvedata"] is True
    assert providers["finnhub"] is True
    assert providers["alpaca"] is True
    assert providers["langsmith"] is False  # LANGSMITH_TRACING is False in mock_settings

    # Security check: Ensure no secret substrings exist in raw response
    raw_text = response.text.lower()
    assert "secret" not in raw_text or "secret_key" not in raw_text
    assert "test_gemini_key" not in raw_text
    assert "test_alpaca_key" not in raw_text


def test_health_with_missing_credentials(client):
    """Health check must succeed even when all provider credentials are empty."""
    empty_settings = Settings(
        GEMINI_API_KEY=None,
        TWELVEDATA_API_KEY=None,
        FINNHUB_API_KEY=None,
        ALPACA_API_KEY=None,
        ALPACA_SECRET_KEY=None,
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
    )
    app.dependency_overrides[get_settings] = lambda: empty_settings

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["providers"]["gemini"] is False
    assert data["providers"]["twelvedata"] is False
    assert data["providers"]["finnhub"] is False
    assert data["providers"]["alpaca"] is False

    app.dependency_overrides.clear()
