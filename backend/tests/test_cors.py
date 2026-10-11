"""Regression test suite for Cross-Origin Resource Sharing (CORS) security and routing.

Verifies:
1. Preflight OPTIONS requests for allowed Vercel and localhost origins return HTTP 200.
2. Disallowed origins return HTTP 400 Bad Request with "Disallowed CORS origin".
3. Preflight mirrors requested headers (e.g. Content-Type) for POST requests.
4. Settings parse CSV or list CORS_ORIGINS from environment variables safely.
5. Wildcard '*' CORS origin is strictly prohibited and raises a ValidationError.
6. Trailing slashes are normalized to prevent browser origin mismatch.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app

client = TestClient(app)

VERCEL_ORIGIN = "https://tradingagent-eight.vercel.app"
DISALLOWED_ORIGIN = "https://unauthorized-external-site.com"


def test_cors_preflight_health_allowed_origin():
    """OPTIONS /health with Vercel origin must return 200 with matching Allow-Origin header."""
    response = client.options(
        "/health",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == VERCEL_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_portfolio_allowed_origin():
    """OPTIONS /api/v1/portfolio with Vercel origin must return 200 with matching Allow-Origin header."""
    response = client.options(
        "/api/v1/portfolio",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == VERCEL_ORIGIN


def test_cors_preflight_analyze_post_allowed_origin():
    """OPTIONS /api/v1/analyze for POST with Content-Type header must succeed."""
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, accept",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == VERCEL_ORIGIN
    assert "content-type" in response.headers.get("access-control-allow-headers", "").lower()


def test_cors_preflight_disallowed_origin_returns_400():
    """OPTIONS request from unlisted domain must return 400 Bad Request."""
    response = client.options(
        "/health",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "Disallowed CORS origin" in response.text
    assert "access-control-allow-origin" not in response.headers


def test_cors_actual_get_health_allowed_origin():
    """Actual GET /health with Vercel origin returns 200 and mirrors Allow-Origin."""
    response = client.get("/health", headers={"Origin": VERCEL_ORIGIN})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == VERCEL_ORIGIN


def test_cors_actual_get_health_disallowed_origin():
    """Actual GET /health with disallowed origin succeeds without Allow-Origin header."""
    response = client.get("/health", headers={"Origin": DISALLOWED_ORIGIN})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_settings_csv_parsing_and_trailing_slash_normalization():
    """Settings must parse comma-separated string and strip trailing slashes."""
    settings = Settings(
        CORS_ORIGINS="https://tradingagent-eight.vercel.app/, http://localhost:3000/ "
    )
    assert settings.CORS_ORIGINS == [
        "https://tradingagent-eight.vercel.app",
        "http://localhost:3000",
    ]


def test_cors_settings_prohibits_wildcard():
    """Settings must reject wildcard '*' to prevent insecure credential exposure."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(CORS_ORIGINS="*")
    assert "Wildcard '*' CORS origin is strictly prohibited" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info2:
        Settings(CORS_ORIGINS=["*"])
    assert "Wildcard '*' CORS origin is strictly prohibited" in str(exc_info2.value)


def test_cors_settings_prohibits_empty_origins():
    """Settings must reject empty origins list."""
    with pytest.raises(ValidationError):
        Settings(CORS_ORIGINS="")
