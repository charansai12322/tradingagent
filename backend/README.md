# AI Trading Agent — Backend Service

A production-style asynchronous **FastAPI** backend for the AI Trading Agent.

Migrated from Google Colab into a modular, decoupled architecture with strict separation between AI reasoning, pre-trade risk controls, and order execution.

---

## Key Features & Safety Guardrails

- **Decoupled Architecture:** 100% free of Google Colab dependencies (`google.colab.userdata` replaced by type-safe `pydantic-settings`).
- **Separation of Reasoning & Execution:** The AI model (Google Gemini 2.5 Flash via LangChain) is strictly advisory; it has **zero execution authority**.
- **Deterministic Risk Engine:** Orders must pass pre-trade risk limits (`MAX_ORDER_NOTIONAL_USD`, `MAX_POSITION_NOTIONAL_USD`, inventory ownership checks, replay deduplication, and proposal TTL expiry) before execution.
- **Master Kill-Switch:** `TRADING_ENABLED=false` by default. Live trading is strictly rejected by configuration validation.
- **Human-in-the-Loop Gateway:** Proposed orders require explicit approval bound to a server-side `proposal_id`.

---

## Local Development & Setup (Windows PowerShell)

### 1. Prerequisites
- **Python**: 3.12 (Python 3.12.10 recommended)
- **PowerShell** 5.1+ or PowerShell Core 7+

### 2. Environment Setup

From the repository root, open PowerShell:

```powershell
# Navigate into backend directory
cd backend

# Create virtual environment with Python 3.12
py -3.12 -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` (this file is ignored by Git):

```powershell
Copy-Item .env.example .env
```

Open `.env` and fill in your API credentials:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
TWELVEDATA_API_KEY=your_twelvedata_api_key_here
FINNHUB_API_KEY=your_finnhub_api_key_here

ALPACA_API_KEY=your_alpaca_paper_key_id_here
ALPACA_SECRET_KEY=your_alpaca_paper_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Safety Controls
TRADING_MODE=paper
TRADING_ENABLED=false
ORDER_APPROVAL_REQUIRED=true
MAX_ORDER_NOTIONAL_USD=100
MAX_POSITION_NOTIONAL_USD=500
```

> [!NOTE]
> You do **not** need all API keys configured just to start the server or inspect `/health`. The server starts safely with missing keys and validates them only when the respective service endpoint is invoked.

### 4. Run Development Server

```powershell
uvicorn app.main:app --reload
```

The server will start at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Instant Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## API Endpoints Reference

### 1. `GET /health`
Instant health check and provider readiness diagnostic. Makes zero external requests and requires zero API keys.

**Example Response:**
```json
{
  "status": "ok",
  "app_env": "development",
  "trading_mode": "paper",
  "trading_enabled": false,
  "order_approval_required": true,
  "providers": {
    "gemini": true,
    "twelvedata": true,
    "finnhub": true,
    "alpaca": true
  },
  "timestamp": "2026-10-11T22:30:00.000000"
}
```

---

### 2. `POST /api/v1/analyze`
Fetches quotes, daily history, RSI, and SMA from TwelveData, recent news from Finnhub, and synthesizes an investment recommendation via Gemini 2.5 Flash.

**Request:**
```json
{
  "symbol": "AAPL"
}
```

**Guarantees:**
- `order_executed` is **always `false`**.
- If recommendation is `BUY` or `SELL`, a `proposed_order` is created with a unique `proposal_id` and 15-minute expiration time.

**Example Response:**
```json
{
  "symbol": "AAPL",
  "recommendation": "BUY",
  "confidence": "Medium",
  "rationale": "AAPL maintains a bullish moving average alignment with RSI at 58.5 (neutral). Recent product news indicates sustained commercial interest.",
  "summary": "Technical momentum remains constructive above 50-day and 200-day SMAs.",
  "indicators": {
    "quote": {
      "symbol": "AAPL",
      "price": 337.50,
      "retrieved_at": "2026-10-11T22:30:00.000000"
    },
    "history": [
      { "date": "2026-10-07", "close": 336.67 },
      { "date": "2026-10-08", "close": 337.59 }
    ],
    "rsi": {
      "time_period": 14,
      "value": 58.52,
      "interpretation": "Neutral (30 <= RSI <= 70)"
    },
    "sma": {
      "sma_50": 322.27,
      "sma_200": 311.53,
      "fast_above_slow": true,
      "trend_regime": "Bullish Moving Average Alignment (50 SMA > 200 SMA)",
      "is_true_crossover": false
    }
  },
  "news": [
    {
      "headline": "Apple reveals major new initiative",
      "source": "Yahoo",
      "datetime": 1791467060
    }
  ],
  "proposed_order": {
    "proposal_id": "prop_8a4f10c7e2b1",
    "symbol": "AAPL",
    "side": "buy",
    "quantity": 1,
    "estimated_price": 337.50,
    "estimated_notional": 337.50,
    "status": "PROPOSED",
    "created_at": "2026-10-11T22:30:00.000000",
    "expires_at": "2026-10-11T22:45:00.000000"
  },
  "order_executed": false,
  "risk_warnings": [
    "Paper simulation only: All recommendations are advisory and require explicit manual approval."
  ],
  "timestamp": "2026-10-11T22:30:00.000000"
}
```

---

### 3. `GET /api/v1/portfolio`
Read-only query of Alpaca Paper balance, cash, buying power, and active equity positions.

---

### 4. `POST /api/v1/orders/approve`
Human-in-the-Loop trade execution gateway.

**Request:**
```json
{
  "proposal_id": "prop_8a4f10c7e2b1",
  "confirm": true
}
```

**Behavior:**
1. Validates that proposal exists and has not expired.
2. Checks that proposal was not already executed (duplicate/replay prevention).
3. Verifies `TRADING_ENABLED=true` (rejects if `false`).
4. Checks order notional $\le$ `MAX_ORDER_NOTIONAL_USD`.
5. Checks position notional $\le$ `MAX_POSITION_NOTIONAL_USD`.
6. Checks share ownership for SELL orders.
7. Submits paper order to Alpaca and returns execution confirmation.

---

## Testing Plan (Phase 3 Preparation)
Detailed test requirements are documented in [tests/README.md](file:///c:/Users/chara/OneDrive/Desktop/projects/tradingagent/tradingagent/backend/tests/README.md).
