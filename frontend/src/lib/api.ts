/**
 * Typed API Client for AI Trading Agent Backend.
 * Communicates exclusively with the FastAPI backend service.
 * Never stores or transmits broker or LLM credentials.
 */

import {
  AnalysisRequest,
  AnalysisResponse,
  HealthResponse,
  OrderApprovalRequest,
  OrderExecutionResult,
  PortfolioResponse,
} from "@/types/trading";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://127.0.0.1:8000";

export class ApiError extends Error {
  public statusCode: number;
  public details?: unknown;

  constructor(message: string, statusCode: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      let errorBody: any = null;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = { message: await res.text() };
      }
      throw new ApiError(
        errorBody?.detail || errorBody?.message || `HTTP ${res.status} error`,
        res.status,
        errorBody
      );
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      err instanceof Error ? err.message : "Failed to connect to backend",
      0
    );
  }
}

export const tradingApi = {
  /**
   * Check backend server health and provider status.
   */
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  /**
   * Request multi-signal AI analysis for a ticker symbol.
   * GUARANTEE: Never executes an order.
   */
  async analyzeStock(symbol: string): Promise<AnalysisResponse> {
    const payload: AnalysisRequest = { symbol: symbol.trim().toUpperCase() };
    return request<AnalysisResponse>("/api/v1/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /**
   * Fetch active paper trading balance and open positions.
   */
  async getPortfolio(): Promise<PortfolioResponse> {
    return request<PortfolioResponse>("/api/v1/portfolio");
  },

  /**
   * Human-in-the-Loop order approval.
   * MUST only be called after explicit user interaction with confirmation modal.
   */
  async approveOrder(proposalId: string, confirm: boolean = true): Promise<OrderExecutionResult> {
    const payload: OrderApprovalRequest = {
      proposal_id: proposalId,
      confirm,
    };
    return request<OrderExecutionResult>("/api/v1/orders/approve", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
