"use client";

import React, { useState } from "react";
import {
  Search,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Newspaper,
  ShieldAlert,
  Clock,
  Sparkles,
  ExternalLink,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { AnalysisResponse, ProposedOrder } from "@/types/trading";
import { formatCurrency, formatDateTime } from "@/lib/formatters";

export interface AnalysisSectionProps {
  currentSymbol: string;
  onSymbolChange: (symbol: string) => void;
  onRunAnalysis: (symbol: string) => Promise<void>;
  analysisResult: AnalysisResponse | null;
  isLoading: boolean;
  error: string | null;
  onOpenOrderModal: (proposal: ProposedOrder) => void;
}

export const AnalysisSection: React.FC<AnalysisSectionProps> = ({
  currentSymbol,
  onSymbolChange,
  onRunAnalysis,
  analysisResult,
  isLoading,
  error,
  onOpenOrderModal,
}) => {
  const [inputVal, setInputVal] = useState(currentSymbol || "AAPL");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = inputVal.trim().toUpperCase();
    if (!clean) {
      setValidationError("Please enter a valid stock ticker symbol.");
      return;
    }
    if (!/^[A-Z0-9.]{1,10}$/.test(clean)) {
      setValidationError("Ticker must be 1-10 uppercase alphanumeric characters (e.g., AAPL, BRK.B).");
      return;
    }
    setValidationError(null);
    onSymbolChange(clean);
    onRunAnalysis(clean);
  };

  const quickPicks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Research Query Header */}
      <section className="bg-chalk border border-stone p-6 rounded-sm shadow-sm">
        <div className="max-w-2xl">
          <div className="text-[11px] font-mono tracking-widest uppercase text-muted mb-1 flex items-center gap-2">
            <span>RESEARCH DESK</span>
            <span className="text-stone">·</span>
            <span>MULTI-SIGNAL ANALYSIS</span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl text-ink font-normal tracking-tight">
            Security Intelligence & Market Synthesis
          </h2>
          <p className="text-xs md:text-sm text-ink/70 mt-1 font-sans">
            Retrieve real-time price quotes, moving averages, relative strength (RSI), and verified news to generate an institutional-grade research dossier.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 flex flex-col sm:flex-row items-stretch sm:items-end gap-3 max-w-xl">
          <div className="flex-1">
            <Input
              label="Stock Ticker Symbol"
              placeholder="e.g. AAPL, NVDA"
              value={inputVal}
              onChange={(e) => {
                setInputVal(e.target.value.toUpperCase());
                if (validationError) setValidationError(null);
              }}
              mono
              error={validationError || undefined}
              hint="US equity ticker symbol (TwelveData & Finnhub)"
              disabled={isLoading}
            />
          </div>
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            className="sm:mb-4 h-9"
          >
            <Search className="w-3.5 h-3.5 mr-1" />
            Analyze Symbol
          </Button>
        </form>

        {/* Quick Picks */}
        <div className="flex items-center gap-2 mt-4 text-xs font-sans text-muted">
          <span>Popular:</span>
          <div className="flex items-center gap-1.5 flex-wrap">
            {quickPicks.map((sym) => (
              <button
                key={sym}
                type="button"
                onClick={() => {
                  setInputVal(sym);
                  setValidationError(null);
                  onSymbolChange(sym);
                  onRunAnalysis(sym);
                }}
                disabled={isLoading}
                className="font-mono text-[11px] px-2 py-0.5 bg-bone hover:bg-stone/40 border border-stone/80 rounded-sm text-ink transition-colors disabled:opacity-50"
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Loading State */}
      {isLoading && (
        <LoadingState
          message={`Conducting multi-signal analysis for ${inputVal || "symbol"}...`}
          subtext="Querying TwelveData price quote, calculating RSI & SMA trend regimes, fetching Finnhub articles, and synthesizing via Gemini."
        />
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          title={`Analysis Failed for ${inputVal}`}
          message={error}
          onRetry={() => onRunAnalysis(inputVal)}
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && !analysisResult && (
        <EmptyState
          title="No Active Research Dossier"
          description="Enter a ticker symbol above or choose one of the popular equities to initiate multi-signal research."
          action={
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setInputVal("AAPL");
                onSymbolChange("AAPL");
                onRunAnalysis("AAPL");
              }}
            >
              Analyze Apple Inc. (AAPL)
            </Button>
          }
        />
      )}

      {/* Structured Analysis Results View */}
      {!isLoading && !error && analysisResult && (
        <div className="space-y-8 animate-fade-in">
          {/* Executive Summary Masthead */}
          <section className="bg-chalk border border-stone p-6 rounded-sm shadow-sm">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-stone/80">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-3xl font-bold tracking-tight text-ink">
                    {analysisResult.symbol}
                  </span>
                  <Badge
                    variant={
                      analysisResult.recommendation === "BUY"
                        ? "buy"
                        : analysisResult.recommendation === "SELL"
                        ? "sell"
                        : "hold"
                    }
                    size="md"
                  >
                    {analysisResult.recommendation}
                  </Badge>
                  <Badge variant="neutral" size="sm">
                    {analysisResult.confidence} CONFIDENCE
                  </Badge>
                </div>
                <div className="flex items-center gap-3 mt-1.5 text-xs font-mono text-muted">
                  <span>Price: ${analysisResult.indicators?.quote?.price?.toFixed(2) || "—"}</span>
                  <span className="text-stone">·</span>
                  <span>Data Timestamp: {formatDateTime(analysisResult.indicators?.quote?.retrieved_at)}</span>
                </div>
              </div>

              {/* Execution Status Notice */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 bg-bone px-3 py-2 rounded-sm border border-stone text-xs">
                <div className="flex items-center gap-1.5 text-ink font-medium">
                  <ShieldAlert className="w-3.5 h-3.5 text-oxide" />
                  <span>Order Executed: <strong className="font-mono text-oxide">FALSE</strong></span>
                </div>
                <span className="text-[11px] text-muted font-sans">
                  Analysis only. Direct execution authority is withheld.
                </span>
              </div>
            </div>

            {/* AI Executive Summary & Rationale */}
            <div className="pt-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-3">
                <div>
                  <h4 className="text-[11px] font-mono tracking-wider uppercase text-muted mb-1">
                    Executive Summary
                  </h4>
                  <p className="font-serif text-lg text-ink font-normal leading-relaxed">
                    {analysisResult.summary}
                  </p>
                </div>

                <div>
                  <h4 className="text-[11px] font-mono tracking-wider uppercase text-muted mb-1">
                    Analytical Rationale
                  </h4>
                  <p className="font-sans text-xs md:text-sm text-ink/80 leading-relaxed whitespace-pre-line bg-bone/40 p-3 rounded-sm border border-stone/60">
                    {analysisResult.rationale}
                  </p>
                </div>
              </div>

              {/* Risk Warnings Panel */}
              <div className="bg-[#A34F3F]/5 border border-oxide/30 rounded-sm p-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-1.5 text-oxide mb-2 font-mono text-xs font-semibold uppercase tracking-wider">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Risk Factors & Warnings</span>
                  </div>
                  {analysisResult.risk_warnings && analysisResult.risk_warnings.length > 0 ? (
                    <ul className="space-y-2 text-xs text-ink/80 font-sans leading-relaxed">
                      {analysisResult.risk_warnings.map((rw, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-oxide mt-0.5">•</span>
                          <span>{rw}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-muted font-sans">
                      No explicit high-volatility anomalies flagged by the risk model.
                    </p>
                  )}
                </div>

                {/* Proposed Order Gateway Callout */}
                {analysisResult.proposed_order && (
                  <div className="mt-4 pt-3 border-t border-oxide/20">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="text-muted font-mono">Proposal:</span>
                      <span className="font-mono font-semibold text-ink">
                        {analysisResult.proposed_order.side} {analysisResult.proposed_order.quantity} @ ${analysisResult.proposed_order.estimated_price?.toFixed(2)}
                      </span>
                    </div>
                    <Button
                      variant="oxide"
                      size="sm"
                      onClick={() => onOpenOrderModal(analysisResult.proposed_order!)}
                      className="w-full text-xs font-sans"
                    >
                      Review Order Proposal
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* Technical Data & Mathematical Indicators Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Technical Indicators: RSI & Moving Averages */}
            <Card
              title="Technical Indicators"
              subtitle="Mathematical indicators from TwelveData series"
              badge={<Badge variant="neutral" size="sm">Algorithmic</Badge>}
            >
              <div className="space-y-4">
                {/* RSI Card */}
                <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-muted">Relative Strength Index (RSI 14)</span>
                    <span className="font-semibold text-ink text-sm">
                      {analysisResult.indicators?.rsi?.value?.toFixed(2) || "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-sans">
                    <span className="text-muted text-[11px]">Interpretation</span>
                    <Badge
                      variant={
                        analysisResult.indicators?.rsi?.interpretation === "Overbought"
                          ? "oxide"
                          : analysisResult.indicators?.rsi?.interpretation === "Oversold"
                          ? "positive"
                          : "hold"
                      }
                      size="sm"
                    >
                      {analysisResult.indicators?.rsi?.interpretation || "Neutral"}
                    </Badge>
                  </div>
                </div>

                {/* SMA Regime Card */}
                <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
                  <div className="flex items-center justify-between text-xs font-mono mb-1">
                    <span className="text-muted">Simple Moving Averages (50 / 200)</span>
                    <Badge
                      variant={
                        analysisResult.indicators?.sma?.trend_regime === "Bullish"
                          ? "positive"
                          : analysisResult.indicators?.sma?.trend_regime === "Bearish"
                          ? "oxide"
                          : "hold"
                      }
                      size="sm"
                    >
                      {analysisResult.indicators?.sma?.trend_regime || "Indeterminate"}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono mt-2 pt-2 border-t border-stone/40">
                    <div>
                      <span className="text-muted block text-[10px]">SMA 50-Day</span>
                      <span className="font-semibold text-ink">
                        ${analysisResult.indicators?.sma?.sma_50?.toFixed(2) || "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted block text-[10px]">SMA 200-Day</span>
                      <span className="font-semibold text-ink">
                        ${analysisResult.indicators?.sma?.sma_200?.toFixed(2) || "—"}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 text-[11px] text-muted font-sans flex items-center justify-between">
                    <span>Crossover Event:</span>
                    <span className="font-mono text-ink">
                      {analysisResult.indicators?.sma?.is_true_crossover ? "Confirmed Active" : "Alignment Only (No Crossing)"}
                    </span>
                  </div>
                </div>

                {/* Price History Snapshot */}
                <div>
                  <h5 className="text-[11px] font-mono tracking-wider uppercase text-muted mb-2">
                    Recent Price Series History
                  </h5>
                  {analysisResult.indicators?.history && analysisResult.indicators.history.length > 0 ? (
                    <div className="border border-stone rounded-sm overflow-hidden text-xs">
                      <table className="w-full text-left font-mono">
                        <thead className="bg-bone text-muted border-b border-stone text-[10px] uppercase">
                          <tr>
                            <th className="py-1 px-3">Date</th>
                            <th className="py-1 px-3 text-right">Close Price</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-stone/40 bg-chalk">
                          {analysisResult.indicators.history.slice(0, 5).map((h, i) => (
                            <tr key={i} className="hover:bg-bone/40">
                              <td className="py-1.5 px-3 text-muted">{h.date}</td>
                              <td className="py-1.5 px-3 text-right font-semibold text-ink">
                                ${h.close?.toFixed(2)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-muted font-sans">No recent historical prices returned.</p>
                  )}
                </div>
              </div>
            </Card>

            {/* Company News & Sentiment */}
            <Card
              title="Verified Market News"
              subtitle="Finnhub headline intelligence with injection sanitization"
              badge={<Badge variant="neutral" size="sm">Finnhub</Badge>}
            >
              {analysisResult.news && analysisResult.news.length > 0 ? (
                <div className="space-y-3.5">
                  {analysisResult.news.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-bone/30 rounded-sm border border-stone/60 hover:border-stone transition-all"
                    >
                      <h5 className="font-serif text-sm text-ink font-normal leading-snug">
                        {item.headline}
                      </h5>
                      {item.summary && (
                        <p className="text-xs text-ink/75 font-sans mt-1 leading-relaxed line-clamp-2">
                          {item.summary}
                        </p>
                      )}
                      <div className="flex items-center justify-between text-[10px] font-mono text-muted mt-2 pt-1.5 border-t border-stone/40">
                        <span>Source: Finnhub Feed</span>
                        {item.datetime && <span>{item.datetime}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-muted text-xs font-sans">
                  <Newspaper className="w-6 h-6 mx-auto mb-2 text-stone stroke-[1.5]" />
                  <p>No recent news articles returned for {analysisResult.symbol} in the 7-day lookback window.</p>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
