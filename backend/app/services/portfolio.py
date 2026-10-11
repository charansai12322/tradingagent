"""Portfolio service integrating Alpaca Paper Trading API.

Read-only retrieval of virtual account balance, cash, buying power, and active positions.
Strictly restricted to Alpaca Paper Trading endpoint.
Never submits orders.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional
import httpx

from app.core.config import Settings, get_settings
from app.schemas.trading import PortfolioPosition, PortfolioResponse

logger = logging.getLogger("tradingagent.portfolio")


class PortfolioServiceError(Exception):
    """Raised when portfolio data retrieval fails."""
    pass


class PortfolioService:
    """Service client for Alpaca paper-trading portfolio inspection."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.ALPACA_BASE_URL.rstrip("/")
        self.api_key = self.settings.ALPACA_API_KEY
        self.secret_key = self.settings.ALPACA_SECRET_KEY
        self.timeout = 10.0

        # Safety verification: strictly enforce paper URL
        if "paper-api.alpaca.markets" not in self.base_url:
            raise PortfolioServiceError(
                f"Insecure base URL '{self.base_url}'. Only 'https://paper-api.alpaca.markets' is permitted."
            )

    def _get_headers(self) -> dict:
        """Construct authentication headers for Alpaca API."""
        if not self.api_key or not self.secret_key:
            raise PortfolioServiceError(
                "ALPACA_API_KEY or ALPACA_SECRET_KEY is missing in backend environment."
            )
        return {
            "APCA-API-KEY-ID": self.api_key.strip(),
            "APCA-API-SECRET-KEY": self.secret_key.strip(),
            "Accept": "application/json",
        }

    async def get_portfolio(self) -> PortfolioResponse:
        """Fetch account balance and open positions from Alpaca paper trading."""
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Fetch Account Details
            try:
                acc_res = await client.get(f"{self.base_url}/v2/account", headers=headers)
                acc_res.raise_for_status()
                acc_data = acc_res.json()
            except httpx.HTTPStatusError as exc:
                logger.error("Alpaca account HTTP status error: %s", exc.response.status_code)
                if exc.response.status_code == 403 or exc.response.status_code == 401:
                    raise PortfolioServiceError("Invalid Alpaca credentials or unauthorized access.")
                raise PortfolioServiceError(f"Alpaca account endpoint failed: {exc}")
            except httpx.HTTPError as exc:
                logger.error("Alpaca account network error: %s", exc)
                raise PortfolioServiceError(f"Failed to connect to Alpaca Paper API: {exc}")

            # 2. Fetch Active Positions
            try:
                pos_res = await client.get(f"{self.base_url}/v2/positions", headers=headers)
                pos_res.raise_for_status()
                pos_data = pos_res.json()
            except httpx.HTTPError as exc:
                logger.error("Alpaca positions network error: %s", exc)
                raise PortfolioServiceError(f"Failed to retrieve positions from Alpaca: {exc}")

        # Sanitize and parse positions
        positions: List[PortfolioPosition] = []
        if isinstance(pos_data, list):
            for p in pos_data:
                try:
                    positions.append(
                        PortfolioPosition(
                            symbol=p.get("symbol", "UNKNOWN"),
                            qty=float(p.get("qty", 0)),
                            avg_entry_price=round(float(p.get("avg_entry_price", 0)), 2),
                            current_price=round(float(p.get("current_price", 0)), 2) if "current_price" in p else None,
                            market_value=round(float(p.get("market_value", 0)), 2) if "market_value" in p else None,
                            unrealized_pl=round(float(p.get("unrealized_pl", 0)), 2) if "unrealized_pl" in p else None,
                            unrealized_plpc=round(float(p.get("unrealized_plpc", 0)), 4) if "unrealized_plpc" in p else None,
                        )
                    )
                except (ValueError, TypeError) as exc:
                    logger.warning("Skipping malformed position item: %s", exc)
                    continue

        return PortfolioResponse(
            account_status=acc_data.get("status", "UNKNOWN"),
            currency=acc_data.get("currency", "USD"),
            cash=round(float(acc_data.get("cash", 0)), 2),
            portfolio_value=round(float(acc_data.get("portfolio_value", 0)), 2),
            buying_power=round(float(acc_data.get("buying_power", 0)), 2),
            positions=positions,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
