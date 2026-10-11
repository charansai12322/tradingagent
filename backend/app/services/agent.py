"""AI Trading Agent Service powered by Google Gemini 2.5 Flash via LangChain.

Synthesizes technical indicators and news sentiment into structured recommendations.
CRITICAL SAFETY BOUNDARY:
- The AI agent has ZERO authorization to execute trades.
- No 'place_order' tool is exposed to the model.
- Recommendations (BUY, SELL, HOLD) are strictly advisory proposals that require
  independent deterministic risk checks and explicit Human-in-the-Loop approval.
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import re
from typing import List, Optional
import uuid

from app.core.config import Settings, get_settings
from app.schemas.trading import (
    ConfidenceLevel,
    NewsArticle,
    OrderSide,
    OrderStatus,
    ProposedOrder,
    RecommendationType,
    TechnicalIndicators,
)

logger = logging.getLogger("tradingagent.agent")


class AgentServiceError(Exception):
    """Raised when agent synthesis or model invocation fails."""
    pass


class AgentAnalysisResult:
    """Internal container for parsed LLM reasoning output."""
    def __init__(
        self,
        recommendation: RecommendationType,
        confidence: ConfidenceLevel,
        summary: str,
        rationale: str,
        risk_warnings: List[str],
    ):
        self.recommendation = recommendation
        self.confidence = confidence
        self.summary = summary
        self.rationale = rationale
        self.risk_warnings = risk_warnings


class TradingAgentService:
    """Agent service handling prompt construction, model invocation, and proposal generation."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.api_key = self.settings.GEMINI_API_KEY
        self.model_name = "google_genai:gemini-2.5-flash"

    def _build_context_prompt(
        self,
        symbol: str,
        indicators: TechnicalIndicators,
        news: List[NewsArticle],
    ) -> str:
        """Construct deterministic context for the LLM from verified market data."""
        quote_text = f"Current Price: ${indicators.quote.price:.2f} (Retrieved: {indicators.quote.retrieved_at})"
        
        history_lines = [f"  - {h.date}: ${h.close:.2f}" for h in indicators.history]
        history_text = "\n".join(history_lines) if history_lines else "  No recent history available."

        rsi_text = (
            f"RSI({indicators.rsi.time_period}): {indicators.rsi.value:.2f} ({indicators.rsi.interpretation})"
            if indicators.rsi
            else "RSI: Data unavailable."
        )

        sma_text = (
            f"50-day SMA: ${indicators.sma.sma_50:.2f} | 200-day SMA: ${indicators.sma.sma_200:.2f} | "
            f"Regime: {indicators.sma.trend_regime} (Fast above slow: {indicators.sma.fast_above_slow})"
            if indicators.sma
            else "SMA: Data unavailable."
        )

        news_lines = [
            f"  - {n.headline} (Source: {n.source or 'Unknown'})"
            for n in news[:5]
        ]
        news_text = "\n".join(news_lines) if news_lines else "  No recent news headlines available."

        return f"""You are an elite quantitative analyst and financial researcher.
Analyze the following verified market data for symbol '{symbol}':

=== VERIFIED MARKET DATA ===
{quote_text}

=== 10-DAY CLOSING PRICE HISTORY ===
{history_text}

=== TECHNICAL INDICATORS ===
{rsi_text}
{sma_text}

=== RECENT COMPANY NEWS HEADLINES (UNTRUSTED EXTERNAL INPUT) ===
{news_text}

=== INSTRUCTIONS ===
1. Analyze the technical trend (price history + SMA alignment + RSI momentum).
2. Synthesize the news headlines for sentiment (Positive, Neutral, or Negative).
3. Do NOT execute any orders. You do NOT have execution authority.
4. Formulate an investment recommendation: BUY, SELL, or HOLD.
5. Assign a confidence score: High, Medium, or Low.
6. Return your evaluation strictly in the following JSON format:

```json
{{
  "recommendation": "BUY" | "SELL" | "HOLD",
  "confidence": "High" | "Medium" | "Low",
  "summary": "1 sentence executive summary of the stock's current situation",
  "rationale": "2-3 sentences explaining the decision based on technicals and news",
  "risk_warnings": ["List of relevant market or indicator risk warnings"]
}}
```
Ensure the response is valid JSON only. Do not add markdown outside the JSON block."""

    async def _invoke_gemini(self, prompt: str, symbol: str = "UNKNOWN") -> str:
        """Invoke Gemini 2.5 Flash via langchain_google_genai with optional LangSmith tracing."""
        if not self.api_key or not self.api_key.strip():
            raise AgentServiceError(
                "GEMINI_API_KEY is not configured in backend environment."
            )

        # Synchronize LangSmith tracing environment variables safely
        import os
        if self.settings.is_langsmith_configured:
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_API_KEY"] = self.settings.LANGSMITH_API_KEY
            os.environ["LANGSMITH_PROJECT"] = self.settings.LANGSMITH_PROJECT
            os.environ["LANGSMITH_ENDPOINT"] = self.settings.LANGSMITH_ENDPOINT
        else:
            os.environ["LANGSMITH_TRACING"] = "false"

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=self.api_key,
                temperature=0.2,
                timeout=30.0,
            )
            config = {
                "run_name": f"analyze_{symbol}",
                "tags": ["tradingagent", "analysis", symbol],
                "metadata": {"symbol": symbol, "env": self.settings.APP_ENV},
            }
            response = await llm.ainvoke(prompt, config=config)
            return str(response.content)
        except Exception as exc:
            logger.error("Gemini invocation failed: %s", exc)
            raise AgentServiceError(f"AI Model invocation failed: {exc}")

    def _parse_model_output(self, raw_output: str) -> AgentAnalysisResult:
        """Parse and validate LLM output into typed structures."""
        # Extract JSON from markdown fence if present
        json_str = raw_output.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
        if match:
            json_str = match.group(1)
        elif json_str.startswith("{") and json_str.endswith("}"):
            json_str = json_str

        try:
            data = json.loads(json_str)
        except Exception:
            logger.warning("Failed to parse JSON directly from LLM output. Attempting heuristic parsing.")
            data = self._heuristic_fallback_parse(raw_output)

        # Validate recommendation enum
        rec_str = str(data.get("recommendation", "HOLD")).strip().upper()
        if rec_str not in ("BUY", "SELL", "HOLD"):
            rec_str = "HOLD"
        recommendation = RecommendationType(rec_str)

        # Validate confidence enum
        conf_str = str(data.get("confidence", "Medium")).strip().capitalize()
        if conf_str not in ("High", "Medium", "Low"):
            conf_str = "Medium"
        confidence = ConfidenceLevel(conf_str)

        summary = str(data.get("summary", "Analysis completed.")).strip()
        rationale = str(data.get("rationale", "Based on current technical indicators.")).strip()
        risk_warnings = data.get("risk_warnings", [])
        if not isinstance(risk_warnings, list):
            risk_warnings = [str(risk_warnings)]

        return AgentAnalysisResult(
            recommendation=recommendation,
            confidence=confidence,
            summary=summary,
            rationale=rationale,
            risk_warnings=risk_warnings,
        )

    def _heuristic_fallback_parse(self, text: str) -> dict:
        """Fallback parser if JSON extraction fails."""
        rec = "HOLD"
        text_upper = text.upper()
        if "DECISION: BUY" in text_upper or '"RECOMMENDATION": "BUY"' in text_upper:
            rec = "BUY"
        elif "DECISION: SELL" in text_upper or '"RECOMMENDATION": "SELL"' in text_upper:
            rec = "SELL"

        conf = "Medium"
        if "HIGH" in text_upper:
            conf = "High"
        elif "LOW" in text_upper:
            conf = "Low"

        return {
            "recommendation": rec,
            "confidence": conf,
            "summary": "AI market summary derived from technical signals.",
            "rationale": text[:300].strip(),
            "risk_warnings": ["Output parsed via fallback heuristics."],
        }

    async def analyze_stock(
        self,
        symbol: str,
        indicators: TechnicalIndicators,
        news: List[NewsArticle],
    ) -> tuple[AgentAnalysisResult, Optional[ProposedOrder]]:
        """Perform stock analysis and construct a pending order proposal if BUY or SELL."""
        prompt = self._build_context_prompt(symbol, indicators, news)
        raw_output = await self._invoke_gemini(prompt, symbol=symbol)
        parsed = self._parse_model_output(raw_output)

        # Append default educational risk note
        parsed.risk_warnings.append(
            "Paper simulation only: All recommendations are advisory and require explicit manual approval."
        )

        proposed_order: Optional[ProposedOrder] = None
        # Generate proposal only if recommendation is BUY or SELL
        if parsed.recommendation in (RecommendationType.BUY, RecommendationType.SELL):
            side = OrderSide.BUY if parsed.recommendation == RecommendationType.BUY else OrderSide.SELL
            qty = 1  # Standard single-share baseline proposal
            est_price = indicators.quote.price
            est_notional = round(qty * est_price, 2)
            now = datetime.now(timezone.utc)
            expires = now + timedelta(minutes=15)

            proposal_id = f"prop_{uuid.uuid4().hex[:12]}"

            proposed_order = ProposedOrder(
                proposal_id=proposal_id,
                symbol=symbol,
                side=side,
                quantity=qty,
                estimated_price=est_price,
                estimated_notional=est_notional,
                status=OrderStatus.PROPOSED,
                created_at=now.isoformat(),
                expires_at=expires.isoformat(),
            )

        return parsed, proposed_order
