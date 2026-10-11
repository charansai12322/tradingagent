"""Market data service integrating TwelveData API.

Fetches quotes, historical time series, RSI, and SMA indicators.
Handles rate limits, network timeouts, data validation, and differentiates
between moving average alignment regimes and true crossover events.
Never fabricates data.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
import httpx

from app.core.config import Settings, get_settings
from app.schemas.trading import (
    PriceHistoryItem,
    PriceQuote,
    RsiIndicator,
    SmaIndicator,
    TechnicalIndicators,
)

logger = logging.getLogger("tradingagent.market_data")


class MarketDataError(Exception):
    """Raised when market data retrieval or validation fails."""
    pass


class MarketDataService:
    """Service client for TwelveData REST API."""

    BASE_URL = "https://api.twelvedata.com"

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.api_key = self.settings.TWELVEDATA_API_KEY
        self.timeout = 10.0

    def _ensure_api_key(self) -> None:
        """Validate presence of TwelveData API key."""
        if not self.api_key or not self.api_key.strip():
            raise MarketDataError(
                "TWELVEDATA_API_KEY is not configured in backend environment."
            )

    async def get_current_price(self, symbol: str) -> PriceQuote:
        """Fetch real-time stock price from TwelveData /price endpoint."""
        self._ensure_api_key()
        url = f"{self.BASE_URL}/price"
        params = {"symbol": symbol, "apikey": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching price for %s: %s", symbol, str(exc))
            raise MarketDataError(f"Failed to connect to market data provider: {exc}")

        if "price" not in data:
            error_msg = data.get("message", "Unknown provider response")
            logger.warning("TwelveData price error for %s: %s", symbol, error_msg)
            raise MarketDataError(f"Could not fetch price for '{symbol}': {error_msg}")

        try:
            price_val = float(data["price"])
        except (ValueError, TypeError):
            raise MarketDataError(f"Malformed price value received for '{symbol}': {data['price']}")

        return PriceQuote(
            symbol=symbol,
            price=round(price_val, 2),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )

    async def get_price_history(self, symbol: str, output_size: int = 10) -> List[PriceHistoryItem]:
        """Fetch recent daily closing prices from TwelveData /time_series."""
        self._ensure_api_key()
        url = f"{self.BASE_URL}/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": str(output_size),
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching time series for %s: %s", symbol, str(exc))
            raise MarketDataError(f"Failed to fetch price history: {exc}")

        if "values" not in data:
            error_msg = data.get("message", "Missing 'values' in time series response")
            logger.warning("TwelveData time series error for %s: %s", symbol, error_msg)
            raise MarketDataError(f"Could not fetch price history for '{symbol}': {error_msg}")

        history: List[PriceHistoryItem] = []
        for item in reversed(data["values"]):  # Chronological order
            try:
                history.append(
                    PriceHistoryItem(
                        date=item["datetime"],
                        close=round(float(item["close"]), 2),
                    )
                )
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed candle for %s: %s", symbol, exc)
                continue

        return history

    async def get_rsi(self, symbol: str, time_period: int = 14) -> RsiIndicator:
        """Fetch RSI(14) from TwelveData /rsi endpoint."""
        self._ensure_api_key()
        url = f"{self.BASE_URL}/rsi"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "time_period": str(time_period),
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching RSI for %s: %s", symbol, str(exc))
            raise MarketDataError(f"Failed to fetch RSI: {exc}")

        if "values" not in data or not data["values"]:
            error_msg = data.get("message", "No RSI values returned")
            raise MarketDataError(f"Could not fetch RSI for '{symbol}': {error_msg}")

        try:
            rsi_val = float(data["values"][0]["rsi"])
        except (ValueError, TypeError, KeyError):
            raise MarketDataError(f"Malformed RSI value received for '{symbol}'")

        if rsi_val > 70:
            interpretation = "Overbought (RSI > 70) — possible downward pressure"
        elif rsi_val < 30:
            interpretation = "Oversold (RSI < 30) — possible upward pressure"
        else:
            interpretation = "Neutral (30 <= RSI <= 70)"

        return RsiIndicator(
            time_period=time_period,
            value=round(rsi_val, 2),
            interpretation=interpretation,
        )

    async def get_sma(self, symbol: str) -> SmaIndicator:
        """Fetch 50-day and 200-day Simple Moving Averages from TwelveData /sma."""
        self._ensure_api_key()
        base_params = {
            "symbol": symbol,
            "interval": "1day",
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res_50 = await client.get(
                    f"{self.BASE_URL}/sma",
                    params={**base_params, "time_period": "50"},
                )
                res_200 = await client.get(
                    f"{self.BASE_URL}/sma",
                    params={**base_params, "time_period": "200"},
                )
                res_50.raise_for_status()
                res_200.raise_for_status()
                data_50 = res_50.json()
                data_200 = res_200.json()
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching SMA for %s: %s", symbol, str(exc))
            raise MarketDataError(f"Failed to fetch SMA: {exc}")

        if "values" not in data_50 or not data_50["values"]:
            raise MarketDataError(f"Missing 50-day SMA for '{symbol}'")
        if "values" not in data_200 or not data_200["values"]:
            raise MarketDataError(f"Missing 200-day SMA for '{symbol}'")

        try:
            sma_50 = float(data_50["values"][0]["sma"])
            sma_200 = float(data_200["values"][0]["sma"])
        except (ValueError, TypeError, KeyError):
            raise MarketDataError(f"Malformed SMA data received for '{symbol}'")

        fast_above_slow = sma_50 > sma_200
        if fast_above_slow:
            trend_regime = "Bullish Moving Average Alignment (50 SMA > 200 SMA)"
        else:
            trend_regime = "Bearish Moving Average Alignment (50 SMA <= 200 SMA)"

        # Check for true historical crossover event if multi-day values exist
        is_true_crossover = False
        if len(data_50["values"]) > 1 and len(data_200["values"]) > 1:
            try:
                prev_50 = float(data_50["values"][1]["sma"])
                prev_200 = float(data_200["values"][1]["sma"])
                # True golden cross: 50 crossed 200 from below
                if prev_50 <= prev_200 and sma_50 > sma_200:
                    is_true_crossover = True
                    trend_regime = "Active Golden Cross Event (50 SMA crossed above 200 SMA)"
                # True death cross: 50 crossed 200 from above
                elif prev_50 >= prev_200 and sma_50 < sma_200:
                    is_true_crossover = True
                    trend_regime = "Active Death Cross Event (50 SMA crossed below 200 SMA)"
            except Exception:
                pass

        return SmaIndicator(
            sma_50=round(sma_50, 2),
            sma_200=round(sma_200, 2),
            fast_above_slow=fast_above_slow,
            trend_regime=trend_regime,
            is_true_crossover=is_true_crossover,
        )

    async def get_technical_indicators(self, symbol: str) -> TechnicalIndicators:
        """Fetch all supported technical indicators for a given symbol."""
        quote = await self.get_current_price(symbol)
        
        # Fetch history, RSI, and SMA with fallback warnings if optional calls fail
        history: List[PriceHistoryItem] = []
        rsi: Optional[RsiIndicator] = None
        sma: Optional[SmaIndicator] = None

        try:
            history = await self.get_price_history(symbol, output_size=10)
        except MarketDataError as exc:
            logger.warning("Price history skipped for %s: %s", symbol, exc)

        try:
            rsi = await self.get_rsi(symbol)
        except MarketDataError as exc:
            logger.warning("RSI skipped for %s: %s", symbol, exc)

        try:
            sma = await self.get_sma(symbol)
        except MarketDataError as exc:
            logger.warning("SMA skipped for %s: %s", symbol, exc)

        return TechnicalIndicators(
            quote=quote,
            history=history,
            rsi=rsi,
            sma=sma,
        )
