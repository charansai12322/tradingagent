# AI Trading Agent — Frontend Web Application

The frontend is a modern web application built with **Next.js (App Router)**, **React**, **TypeScript**, and **Tailwind CSS**.

It serves as the user-facing interface for market analysis, technical indicators, news sentiment, portfolio inspection, and Human-in-the-Loop paper trading approvals.

---

## Security Architecture & Separation of Concerns

1. **Zero Secret Footprint:** Private provider keys (Google Gemini, TwelveData, Finnhub, Alpaca, LangSmith) are **never** stored or accessible on the frontend.
2. **Backend Gateway:** The frontend communicates strictly with the local FastAPI backend API via `NEXT_PUBLIC_API_BASE_URL`.
3. **No Direct Execution:** The frontend cannot submit orders on component mounting or background effects. Order submission requires explicit user interaction with a dedicated confirmation modal.

---

## Local Setup & Development

### 1. Prerequisites
- **Node.js**: v18.17+ (v20+ recommended)
- **npm**: v9+ (or pnpm / yarn)

### 2. Environment Configuration
Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Ensure `NEXT_PUBLIC_API_BASE_URL` points to your active backend (default: `http://127.0.0.1:8000`):

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 3. Installation & Run

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start local development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Frontend Monorepo Structure

```text
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx         # Root layout and theme definition
│   │   ├── page.tsx           # Health diagnostic & foundation landing view
│   │   └── globals.css        # Tailwind styling & dark-theme tokens
│   ├── components/            # Reusable UI primitives (buttons, modals, badges)
│   ├── features/              # Domain-specific feature modules
│   │   ├── analysis/          # Technical indicators, quotes & AI rationale
│   │   ├── portfolio/         # Balance, buying power & positions table
│   │   └── orders/            # Human-in-the-Loop approval modal & receipts
│   ├── lib/
│   │   └── api.ts             # Strongly-typed API client for backend routes
│   ├── hooks/                 # Custom React hooks
│   └── types/
│       └── trading.ts         # TypeScript interfaces matching backend schemas
├── public/                    # Static assets
├── .env.example               # Template environment configuration
├── package.json               # Package dependencies & scripts
├── tsconfig.json              # TypeScript configuration
└── README.md                  # This documentation
```

---

## Available Scripts

- `npm run dev`: Starts local development server on port 3000 with hot reloading.
- `npm run build`: Compiles production build.
- `npm run start`: Starts production server.
- `npm run lint`: Runs Next.js ESLint checks.
