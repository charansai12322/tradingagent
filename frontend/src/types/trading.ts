/**
 * TypeScript Data Contracts for AI Trading Agent Frontend.
 * Strictly synchronizes with backend/app/schemas/trading.py.
 */

export type RecommendationType = "BUY" | "SELL" | "HOLD";
export type ConfidenceLevel = "High" | "Medium" | "Low";
export type OrderSide = "buy" | "sell";
export type OrderStatus = "PROPOSED" | "APPROVED" | "REJECTED" | "EXECUTED" | "EXPIRED";

export interface PriceQuote {
  symbol: string;
  price: number;
  retrieved_at: string;
}

export interface PriceHistoryItem {
  date: string;
  close: number;
}

export interface RsiIndicator {
  time_period: number;
  value: number;
  interpretation: string;
}

export interface SmaIndicator {
  sma_50: number;
  sma_200: number;
  fast_above_slow: boolean;
  trend_regime: string;
  is_true_crossover: boolean;
}

export interface TechnicalIndicators {
  quote: PriceQuote;
  history: PriceHistoryItem[];
  rsi?: RsiIndicator;
  sma?: SmaIndicator;
}

export interface NewsArticle {
  headline: string;
  summary?: string;
  source?: string;
  url?: string;
  datetime?: number;
  category?: string;
}

export interface ProposedOrder {
  proposal_id: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  estimated_price: number;
  estimated_notional: number;
  status: OrderStatus;
  created_at: string;
  expires_at: string;
}

export interface AnalysisRequest {
  symbol: string;
}

export interface AnalysisResponse {
  symbol: string;
  recommendation: RecommendationType;
  confidence: ConfidenceLevel;
  rationale: string;
  summary: string;
  indicators: TechnicalIndicators;
  news: NewsArticle[];
  proposed_order?: ProposedOrder;
  order_executed: boolean; // Always false for analysis requests
  risk_warnings: string[];
  timestamp: string;
}

export interface OrderApprovalRequest {
  proposal_id: string;
  confirm: boolean;
}

export interface RiskCheckResult {
  passed: boolean;
  proposal_id: string;
  checks_performed: string[];
  rejection_reasons: string[];
  evaluated_at: string;
}

export interface OrderExecutionResult {
  success: boolean;
  proposal_id: string;
  order_id?: string;
  client_order_id?: string;
  symbol: string;
  side: string;
  quantity: number;
  filled_status: string;
  executed_at: string;
  message: string;
}

export interface PortfolioPosition {
  symbol: string;
  qty: number;
  avg_entry_price: number;
  current_price?: number;
  market_value?: number;
  unrealized_pl?: number;
  unrealized_plpc?: number;
}

export interface PortfolioResponse {
  account_status: string;
  currency: string;
  cash: number;
  portfolio_value: number;
  buying_power: number;
  positions: PortfolioPosition[];
  timestamp: string;
}

export interface ProviderStatus {
  gemini: boolean;
  twelvedata: boolean;
  finnhub: boolean;
  alpaca: boolean;
  langsmith?: boolean;
}

export interface HealthResponse {
  status: string;
  app_env: string;
  trading_mode: string;
  trading_enabled: boolean;
  order_approval_required: boolean;
  providers: ProviderStatus;
  timestamp: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}
