# AI Trading Agent — Monorepo Architecture

An enterprise-grade, full-stack quantitative trading assistant and market analysis platform.

Originally prototyped as an experimental Google Colab notebook (`tradingagent.ipynb`), this repository has been restructured into a production-style monorepo featuring a decoupled **FastAPI backend** and a modern **Next.js frontend**.

---

## 1. Project Overview & Capabilities

The system integrates multi-modal market intelligence to assist equity analysis and simulated trade execution:
- **Real-Time Stock Quotes & Historical Candles:** Integrated via TwelveData REST API.
- **Quantitative Technical Indicators:** 14-period RSI and 50/200-day Simple Moving Average trend evaluation.
- **Company News & Sentiment:** Sanitized news feeds retrieved via Finnhub REST API.
- **AI Synthesis & Rationale:** Google Gemini 2.5 Flash (`google_genai:gemini-2.5-flash`) via LangChain evaluates multi-signal context into structured recommendations (BUY, SELL, HOLD).
- **Human-in-the-Loop Paper Execution:** Strict separation between advisory AI proposals and order execution on Alpaca Paper Trading. Orders require deterministic risk clearance and explicit user confirmation.

---

## 2. Monorepo Architecture & Directory Structure

```text
tradingagent/
│
├── backend/                         # FastAPI Python Service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # Server entrypoint & CORS middleware
│   │   ├── api/
│   │   │   └── routes.py            # API route controllers (/health, /analyze, /portfolio, /orders/approve)
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings & environment validation
│   │   │   └── logging_config.py    # Structured logging with credential redaction
│   │   ├── schemas/
│   │   │   └── trading.py           # Pydantic contracts & request/response schemas
│   │   ├── services/
│   │   │   ├── agent.py             # Gemini / LangChain synthesis service (advisory only)
│   │   │   ├── market_data.py       # TwelveData client (quotes, history, RSI, SMA)
│   │   │   ├── news.py              # Finnhub client with untrusted text sanitization
│   │   │   └── portfolio.py         # Read-only Alpaca Paper balance & positions
│   │   └── trading/
│   │       ├── risk.py              # Deterministic Pre-Trade Risk Engine & ProposalRegistry
│   │       └── execution.py         # Guarded Alpaca Paper order execution service
│   ├── tests/
│   │   └── README.md                # Phase 3 testing specifications & test suites
│   ├── .env.example                 # Backend environment variable template
│   ├── .gitignore                   # Backend Git ignore rules
│   ├── requirements.txt             # Pinned Python package dependencies
│   └── README.md                    # Detailed backend guide & PowerShell setup
│
├── frontend/                        # Next.js Web Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx           # Global root layout & theme
│   │   │   ├── page.tsx             # Diagnostic landing page & backend connection check
│   │   │   └── globals.css          # Tailwind CSS design system tokens
│   │   ├── components/              # Shared UI primitives
│   │   ├── features/                # Domain modules (analysis, portfolio, orders)
│   │   ├── lib/
│   │   │   └── api.ts               # Strongly-typed backend API client
│   │   ├── hooks/                   # React hooks
│   │   └── types/
│   │       └── trading.ts           # TypeScript interfaces matching backend schemas
│   ├── public/                      # Static assets
│   ├── .env.example                 # Frontend environment variable template
│   ├── .gitignore                   # Frontend Git ignore rules
│   ├── package.json                 # Next.js dependencies & scripts
│   ├── tsconfig.json                # TypeScript compiler configuration
│   └── README.md                    # Detailed frontend guide & setup
│
├── tradingagent.ipynb               # Original Google Colab notebook (preserved)
├── README.md                        # Root project overview (this file)
└── .gitignore                       # Root Git ignore rules
```

---

## 3. Technology Stack

| Layer | Primary Technologies |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2, Pydantic Settings, HTTPX, LangChain, Google GenAI SDK |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide Icons |
| **External Providers** | Google Gemini 2.5 Flash, TwelveData API, Finnhub API, Alpaca Paper Trading API |
| **Observability** | LangSmith (optional tracing), Python structured logging |

---

## 4. Trading Safety & Compliance Model

The system operates under a strict zero-trust financial safety model:

1. **AI Cannot Execute Orders:** The LangChain agent prompt contains **no execution tools**. The model is an advisor, not an execution broker.
2. **Analysis Never Trades:** Calling `POST /api/v1/analyze` yields an advisory proposal; `order_executed` is strictly guaranteed to be `false`.
3. **Deterministic Pre-Trade Risk Checks:** Every proposed order must pass independent code checks before submission:
   - Master kill-switch check (`TRADING_ENABLED=true`)
   - Paper-mode check (`TRADING_MODE="paper"`)
   - Maximum single-order notional (`MAX_ORDER_NOTIONAL_USD`, default $100)
   - Maximum ticker position exposure (`MAX_POSITION_NOTIONAL_USD`, default $500)
   - Inventory check (SELL orders require owned shares)
   - Replay/duplicate order deduplication
   - Proposal TTL expiration (15-minute time window)
4. **Human-in-the-Loop Gate:** A trade can only be submitted when a human client explicitly signs off on a server-generated `proposal_id` via `POST /api/v1/orders/approve`.
5. **Live Trading Prohibited:** Configuration strictly rejects live Alpaca endpoints or non-paper modes in this phase.

---

## 5. Local Setup & Quickstart

### Prerequisites
- **Python**: 3.12+ (e.g. Python 3.12.10)
- **Node.js**: v18.17+ (v20+ recommended)
- **Git**

### Step 1: Start the Backend (PowerShell)
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env
# Edit .env and paste your API keys

# Start FastAPI server
uvicorn app.main:app --reload
```
Backend will be available at: `http://127.0.0.1:8000`  
Interactive documentation at: `http://127.0.0.1:8000/docs`

### Step 2: Start the Frontend (Separate Terminal)
```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local

# Start Next.js development server
npm run dev
```
Frontend will be available at: `http://localhost:3000`

---

## 6. API Endpoints Overview

| Method | Path | Description | Safety Guarantee |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Instant service diagnostic & provider flags | Requires 0 keys; 0 network calls |
| `POST` | `/api/v1/analyze` | Gathers indicators & news; runs Gemini analysis | **`order_executed: false`**; never places trades |
| `GET` | `/api/v1/portfolio` | Fetches Alpaca Paper equity, cash & positions | Read-only; never trades |
| `POST` | `/api/v1/orders/approve` | Human-in-the-Loop paper trade execution gate | Enforces risk limits; requires `TRADING_ENABLED=true` |

---

## 7. Current Limitations & Phase 3 Roadmap

- **API Rate Limits:** TwelveData free tier allows 8 requests/minute. Running consecutive analyses without delay can trigger rate limiting.
- **Execution Disabled by Default:** `TRADING_ENABLED` is set to `false`. Orders cannot be submitted to Alpaca until manually enabled in `.env`.
- **Phase 3 Testing Plan:** Phase 3 will implement comprehensive automated tests with mocked provider fixtures (`respx`, `pytest`). See [backend/tests/README.md](file:///c:/Users/chara/OneDrive/Desktop/projects/tradingagent/tradingagent/backend/tests/README.md).
