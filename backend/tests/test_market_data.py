"""Tests for TwelveData Market Data Service with deterministic mocked responses."""

import pytest
import respx
from httpx import Response

from app.core.config import Settings
from app.services.market_data import MarketDataError, MarketDataService


@pytest.fixture
def market_settings():
    return Settings(
        TWELVEDATA_API_KEY="test_twelvedata_mock_key",
        TRADING_MODE="paper",
        TRADING_ENABLED=False,
    )


@pytest.mark.asyncio
async def test_get_current_price_success(market_settings):
    """Real-time quote parsed correctly from valid TwelveData response."""
    svc = MarketDataService(market_settings)

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get("https://api.twelvedata.com/price").mock(
            return_value=Response(200, json={"price": "189.95"})
        )
        quote = await svc.get_current_price("AAPL")
        assert quote.symbol == "AAPL"
        assert quote.price == 189.95
        assert quote.retrieved_at is not None


@pytest.mark.asyncio
async def test_get_current_price_missing_field(market_settings):
    """When TwelveData returns error message without price, raise MarketDataError."""
    svc = MarketDataService(market_settings)

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get("https://api.twelvedata.com/price").mock(
            return_value=Response(200, json={"code": 404, "message": "Symbol not found"})
        )
        with pytest.raises(MarketDataError) as exc_info:
            await svc.get_current_price("FAKESYMBOL")
        assert "Could not fetch price" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_current_price_missing_api_key():
    """Service must raise MarketDataError if API key is not configured."""
    svc = MarketDataService(Settings(TWELVEDATA_API_KEY=None, TRADING_MODE="paper"))
    with pytest.raises(MarketDataError) as exc_info:
        await svc.get_current_price("AAPL")
    assert "not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_price_history_sorted(market_settings):
    """Time series candles must be reversed into chronological order."""
    svc = MarketDataService(market_settings)

    mock_data = {
        "values": [
            {"datetime": "2026-10-08", "close": "190.50"},
            {"datetime": "2026-10-07", "close": "188.20"},
            {"datetime": "2026-10-06", "close": "185.00"},
        ]
    }

    with respx.mock(assert_all_called=True) as respx_mock:
        respx_mock.get("https://api.twelvedata.com/time_series").mock(
            return_value=Response(200, json=mock_data)
        )
        history = await svc.get_price_history("AAPL", output_size=3)
        assert len(history) == 3
        # Chronological order assertion
        assert history[0].date == "2026-10-06"
        assert history[0].close == 185.00
        assert history[2].date == "2026-10-08"
        assert history[2].close == 190.50


@pytest.mark.asyncio
async def test_get_rsi_boundaries(market_settings):
    """RSI interpretation must correctly categorize overbought, oversold, and neutral."""
    svc = MarketDataService(market_settings)

    with respx.mock() as respx_mock:
        # Overbought case (>70)
        respx_mock.get("https://api.twelvedata.com/rsi").mock(
            return_value=Response(200, json={"values": [{"rsi": "78.4"}]})
        )
        rsi_over = await svc.get_rsi("AAPL")
        assert rsi_over.value == 78.4
        assert "Overbought" in rsi_over.interpretation

        # Oversold case (<30)
        respx_mock.get("https://api.twelvedata.com/rsi").mock(
            return_value=Response(200, json={"values": [{"rsi": "22.1"}]})
        )
        rsi_under = await svc.get_rsi("AAPL")
        assert rsi_under.value == 22.1
        assert "Oversold" in rsi_under.interpretation

        # Neutral case
        respx_mock.get("https://api.twelvedata.com/rsi").mock(
            return_value=Response(200, json={"values": [{"rsi": "55.0"}]})
        )
        rsi_neutral = await svc.get_rsi("AAPL")
        assert rsi_neutral.value == 55.0
        assert "Neutral" in rsi_neutral.interpretation


@pytest.mark.asyncio
async def test_get_sma_alignment_and_crossover_event(market_settings):
    """SMA must differentiate standard moving average alignment from a true crossover event."""
    svc = MarketDataService(market_settings)

    # 1. Standard Bullish alignment (no crossover)
    data_50_static = {"values": [{"sma": "210.0"}, {"sma": "208.0"}]}
    data_200_static = {"values": [{"sma": "190.0"}, {"sma": "189.0"}]}

    with respx.mock() as respx_mock:
        respx_mock.get("https://api.twelvedata.com/sma").mock(
            side_effect=[
                Response(200, json=data_50_static),
                Response(200, json=data_200_static),
            ]
        )
        sma_align = await svc.get_sma("AAPL")
        assert sma_align.fast_above_slow is True
        assert sma_align.is_true_crossover is False
        assert "Bullish Moving Average Alignment" in sma_align.trend_regime

    # 2. Active Golden Cross event (50 SMA crossed above 200 SMA)
    # Yesterday: 50 was 188, 200 was 189 (50 <= 200)
    # Today: 50 is 191, 200 is 190 (50 > 200)
    data_50_cross = {"values": [{"sma": "191.0"}, {"sma": "188.0"}]}
    data_200_cross = {"values": [{"sma": "190.0"}, {"sma": "189.0"}]}

    with respx.mock() as respx_mock:
        respx_mock.get("https://api.twelvedata.com/sma").mock(
            side_effect=[
                Response(200, json=data_50_cross),
                Response(200, json=data_200_cross),
            ]
        )
        sma_cross = await svc.get_sma("AAPL")
        assert sma_cross.fast_above_slow is True
        assert sma_cross.is_true_crossover is True
        assert "Active Golden Cross Event" in sma_cross.trend_regime


@pytest.mark.asyncio
async def test_get_technical_indicators_resilience(market_settings):
    """get_technical_indicators must return valid quote even if RSI or SMA fails."""
    svc = MarketDataService(market_settings)

    with respx.mock() as respx_mock:
        respx_mock.get("https://api.twelvedata.com/price").mock(
            return_value=Response(200, json={"price": "150.00"})
        )
        respx_mock.get("https://api.twelvedata.com/time_series").mock(
            return_value=Response(500, text="Internal Error")
        )
        respx_mock.get("https://api.twelvedata.com/rsi").mock(
            return_value=Response(429, text="Rate limit exceeded")
        )
        respx_mock.get("https://api.twelvedata.com/sma").mock(
            return_value=Response(500, text="Server Error")
        )

        indicators = await svc.get_technical_indicators("AAPL")
        assert indicators.quote.price == 150.00
        assert indicators.history == []
        assert indicators.rsi is None
        assert indicators.sma is None
