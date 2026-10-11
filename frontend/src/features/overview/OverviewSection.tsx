"use client";

import React from "react";
import {
  ArrowUpRight,
  Shield,
  Activity,
  Search,
  AlertCircle,
  Database,
  Lock,
  Layers,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { HealthResponse, PortfolioResponse, AnalysisResponse } from "@/types/trading";
import { formatCurrency, formatDateTime } from "@/lib/formatters";

export interface OverviewSectionProps {
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: string | null;
  portfolio: PortfolioResponse | null;
  portfolioLoading: boolean;
  portfolioError: string | null;
  recentAnalyses: AnalysisResponse[];
  onSelectTicker: (ticker: string) => void;
  onNavigateTab: (tab: "analysis" | "portfolio" | "orders" | "status") => void;
  onRefreshAll: () => void;
}

export const OverviewSection: React.FC<OverviewSectionProps> = ({
  health,
  healthLoading,
  healthError,
  portfolio,
  portfolioLoading,
  portfolioError,
  recentAnalyses,
  onSelectTicker,
  onNavigateTab,
  onRefreshAll,
}) => {
  const [tickerInput, setTickerInput] = React.useState("");

  const handleQuickSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (tickerInput.trim()) {
      onSelectTicker(tickerInput.trim().toUpperCase());
      onNavigateTab("analysis");
    }
  };

  const curatedWatchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "SPY"];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Editorial Lead / Dispatch */}
      <section className="border-b border-stone pb-6 pt-2 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div className="max-w-2xl">
          <div className="text-[11px] font-mono tracking-widest uppercase text-muted mb-1.5 flex items-center gap-2">
            <span>EDITORIAL WORKSTATION</span>
            <span className="text-stone">·</span>
            <span>SYSTEM DISPATCH</span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl text-ink font-normal tracking-tight leading-snug">
            Research before acting. Make risk visible. Never confuse predictions with facts.
          </h2>
          <p className="text-xs md:text-sm text-ink/70 mt-2 font-sans leading-relaxed">
            CHAAI synthesizes multi-timeframe price action, moving-average trends, and verified financial news into structured research dossiers. All trades are guarded by a deterministic pre-trade risk engine with mandatory human approval.
          </p>
        </div>

        {/* Quick Ticker Dispatch Box */}
        <div className="w-full lg:w-80 bg-chalk border border-stone p-4 rounded-sm shadow-sm flex-shrink-0">
          <label className="text-[10px] font-mono tracking-wider uppercase text-muted block mb-1.5">
            Quick Market Research
          </label>
          <form onSubmit={handleQuickSearch} className="flex gap-2">
            <input
              type="text"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL, NVDA"
              maxLength={10}
              className="w-full bg-bone border border-stone px-3 py-1.5 text-xs font-mono uppercase text-ink placeholder:text-muted/60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ink rounded-sm"
            />
            <Button type="submit" size="sm" variant="primary">
              <Search className="w-3 h-3" />
            </Button>
          </form>
          <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
            <span className="text-[10px] text-muted font-mono">Sample:</span>
            {curatedWatchlist.slice(0, 4).map((sym) => (
              <button
                key={sym}
                onClick={() => {
                  onSelectTicker(sym);
                  onNavigateTab("analysis");
                }}
                className="text-[10px] font-mono text-ink/80 hover:text-oxide px-1.5 py-0.5 bg-bone/70 hover:bg-bone border border-stone/60 rounded-sm transition-colors"
              >
                {sym}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Primary 3-Pillar Workspace Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pillar 1: Diagnostic Readiness */}
        <Card
          title="Service Health"
          subtitle="Real-time backend readiness"
          badge={
            healthLoading ? (
              <Badge variant="warning" size="sm">Connecting</Badge>
            ) : health ? (
              <Badge variant="positive" size="sm">Online</Badge>
            ) : (
              <Badge variant="oxide" size="sm">Unreachable</Badge>
            )
          }
        >
          <div className="space-y-3 text-xs font-sans">
            <div className="flex items-center justify-between pb-2 border-b border-stone/60">
              <span className="text-muted">Environment</span>
              <span className="font-mono text-ink font-medium">
                {health?.app_env || "Unknown"}
              </span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-stone/60">
              <span className="text-muted">Trading Killswitch</span>
              <span className="font-mono text-oxide font-medium">
                {health?.trading_enabled ? "Active (Risk)" : "DISABLED (Safe)"}
              </span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-stone/60">
              <span className="text-muted">Human Approval</span>
              <span className="font-mono text-positive font-medium">
                {health?.order_approval_required ? "MANDATORY" : "Bypassed"}
              </span>
            </div>
            <div className="flex items-center justify-between pt-1">
              <span className="text-muted">Active Providers</span>
              <span className="font-mono text-ink">
                {health?.providers
                  ? Object.values(health.providers).filter(Boolean).length + " configured"
                  : "0 available"}
              </span>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigateTab("status")}
              className="w-full mt-2 text-xs border border-stone/80 hover:bg-bone"
            >
              Inspect Diagnostic Panel
              <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </Card>

        {/* Pillar 2: Real Account Summary */}
        <Card
          title="Paper Portfolio"
          subtitle="Read-only Alpaca ledger"
          badge={
            portfolio?.account_status ? (
              <Badge variant="neutral" size="sm">{portfolio.account_status}</Badge>
            ) : (
              <Badge variant="muted" size="sm">Paper</Badge>
            )
          }
        >
          <div className="space-y-3 text-xs font-sans">
            {portfolioLoading ? (
              <p className="text-muted text-xs py-4 text-center">Loading account balance...</p>
            ) : portfolioError ? (
              <div className="py-2 text-oxide text-xs">
                <p className="font-medium">Portfolio Unavailable</p>
                <p className="text-[11px] text-muted mt-0.5">{portfolioError}</p>
              </div>
            ) : portfolio ? (
              <>
                <div className="flex items-center justify-between pb-2 border-b border-stone/60">
                  <span className="text-muted">Portfolio Value</span>
                  <span className="font-mono text-ink font-semibold text-sm">
                    {formatCurrency(portfolio.portfolio_value, portfolio.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-stone/60">
                  <span className="text-muted">Cash Available</span>
                  <span className="font-mono text-ink">
                    {formatCurrency(portfolio.cash, portfolio.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-stone/60">
                  <span className="text-muted">Buying Power</span>
                  <span className="font-mono text-ink">
                    {formatCurrency(portfolio.buying_power, portfolio.currency)}
                  </span>
                </div>
                <div className="flex items-center justify-between pt-1">
                  <span className="text-muted">Open Positions</span>
                  <span className="font-mono text-ink font-medium">
                    {portfolio.positions?.length || 0} assets
                  </span>
                </div>
              </>
            ) : (
              <p className="text-muted text-xs py-2">
                Connect backend to view paper portfolio balance.
              </p>
            )}

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigateTab("portfolio")}
              className="w-full mt-2 text-xs border border-stone/80 hover:bg-bone"
            >
              View Open Holdings
              <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </Card>

        {/* Pillar 3: Architectural Risk Gate */}
        <Card
          title="Risk Policy"
          subtitle="Non-negotiable trade boundaries"
          borderAccent
        >
          <div className="space-y-2.5 text-xs text-ink/80 font-sans leading-relaxed">
            <div className="flex items-start gap-2">
              <Lock className="w-3.5 h-3.5 text-oxide flex-shrink-0 mt-0.5" />
              <p>
                <strong className="text-ink">Global Killswitch:</strong> Order placement is disabled (<code className="font-mono text-[11px] bg-bone px-1 py-0.5 rounded">TRADING_ENABLED=false</code>).
              </p>
            </div>
            <div className="flex items-start gap-2">
              <Shield className="w-3.5 h-3.5 text-moss flex-shrink-0 mt-0.5" />
              <p>
                <strong className="text-ink">Paper Sandbox:</strong> Live trading is prohibited by hardcoded configuration guard.
              </p>
            </div>
            <div className="flex items-start gap-2">
              <Layers className="w-3.5 h-3.5 text-muted flex-shrink-0 mt-0.5" />
              <p>
                <strong className="text-ink">Notional Cap:</strong> Maximum $100 per order, $500 max symbol exposure.
              </p>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => onNavigateTab("orders")}
              className="w-full mt-2 text-xs border border-stone/80 hover:bg-bone"
            >
              Inspect Order Governance
              <ChevronRight className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </Card>
      </div>

      {/* Recent Session Research Dossiers (if any) */}
      <section className="pt-2">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-stone">
          <div className="flex items-center gap-2">
            <h3 className="font-serif text-lg text-ink font-normal tracking-tight">
              Session Research Dossiers
            </h3>
            <span className="text-xs font-mono text-muted">
              ({recentAnalyses.length} completed)
            </span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onNavigateTab("analysis")}
          >
            Launch Research Desk
            <ArrowUpRight className="w-3 h-3 ml-1" />
          </Button>
        </div>

        {recentAnalyses.length === 0 ? (
          <div className="bg-chalk/60 border border-dashed border-stone rounded-sm p-6 text-center">
            <p className="text-xs text-muted font-sans max-w-md mx-auto">
              No ticker analyses performed in this session yet. Select any symbol above to initiate comprehensive technical and sentiment research.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentAnalyses.map((item, idx) => (
              <div
                key={`${item.symbol}-${idx}`}
                onClick={() => {
                  onSelectTicker(item.symbol);
                  onNavigateTab("analysis");
                }}
                className="bg-chalk border border-stone p-4 rounded-sm hover:border-ink transition-all cursor-pointer shadow-sm group"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="font-mono text-base font-bold text-ink group-hover:text-oxide transition-colors">
                      {item.symbol}
                    </span>
                    <span className="text-[11px] font-mono text-muted block">
                      ${item.indicators?.quote?.price?.toFixed(2) || "—"}
                    </span>
                  </div>
                  <Badge
                    variant={
                      item.recommendation === "BUY"
                        ? "buy"
                        : item.recommendation === "SELL"
                        ? "sell"
                        : "hold"
                    }
                    size="sm"
                  >
                    {item.recommendation}
                  </Badge>
                </div>

                <p className="text-xs text-ink/75 font-sans line-clamp-2 leading-relaxed mb-3">
                  {item.summary || item.rationale}
                </p>

                <div className="flex items-center justify-between text-[10px] font-mono text-muted border-t border-stone/60 pt-2">
                  <span>Confidence: {item.confidence}</span>
                  <span>{formatDateTime(item.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
