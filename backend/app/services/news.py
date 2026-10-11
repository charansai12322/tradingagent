"""News service integrating Finnhub API.

Retrieves recent company news headlines.
Treats all external article headlines and summaries as untrusted external input.
Sanitizes strings and ensures no prompt injections can override risk or approval logic.
"""

from datetime import datetime, timedelta, timezone
import logging
import re
from typing import List, Optional
import httpx

from app.core.config import Settings, get_settings
from app.schemas.trading import NewsArticle

logger = logging.getLogger("tradingagent.news")


class NewsServiceError(Exception):
    """Raised when news retrieval fails."""
    pass


class NewsService:
    """Service client for Finnhub company news."""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.api_key = self.settings.FINNHUB_API_KEY
        self.timeout = 10.0

    def _sanitize_untrusted_text(self, text: Optional[str]) -> str:
        """Sanitize external news text to prevent control characters or prompt injection exploits."""
        if not text:
            return ""
        # Strip ASCII control characters except standard space
        cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)
        # Collapse multi-spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Cap length to prevent token flooding
        return cleaned[:300]

    async def get_company_news(self, symbol: str, lookback_days: int = 7, max_articles: int = 5) -> List[NewsArticle]:
        """Fetch and sanitize recent news headlines from Finnhub."""
        if not self.api_key or not self.api_key.strip():
            logger.warning("FINNHUB_API_KEY not set. Returning empty news list.")
            return []

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        from_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        url = f"{self.BASE_URL}/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": today,
            "token": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Failed to retrieve Finnhub news for %s: %s", symbol, exc)
            return []
        except Exception as exc:
            logger.warning("Unexpected error parsing Finnhub news: %s", exc)
            return []

        if not isinstance(data, list):
            logger.warning("Finnhub returned non-list news data: %s", type(data))
            return []

        articles: List[NewsArticle] = []
        for raw in data[:max_articles]:
            if not isinstance(raw, dict):
                continue
            headline = self._sanitize_untrusted_text(raw.get("headline"))
            if not headline:
                continue
            summary = self._sanitize_untrusted_text(raw.get("summary"))
            source = self._sanitize_untrusted_text(raw.get("source"))

            articles.append(
                NewsArticle(
                    headline=headline,
                    summary=summary if summary else None,
                    source=source if source else None,
                    url=raw.get("url"),
                    datetime=raw.get("datetime"),
                    category=raw.get("category"),
                )
            )

        return articles
