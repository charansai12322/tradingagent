"use client";

import React from "react";
import {
  Wallet,
  ArrowUpRight,
  ShieldAlert,
  RefreshCw,
  FolderOpen,
  DollarSign,
  Briefcase,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/LoadingState";
import { PortfolioResponse } from "@/types/trading";
import { formatCurrency, formatNumber, formatPercentage, formatDateTime } from "@/lib/formatters";

export interface PortfolioSectionProps {
  portfolio: PortfolioResponse | null;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
  onSelectTicker: (ticker: string) => void;
}

export const PortfolioSection: React.FC<PortfolioSectionProps> = ({
  portfolio,
  isLoading,
  error,
  onRefresh,
  onSelectTicker,
}) => {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Portfolio Masthead */}
      <section className="bg-chalk border border-stone p-6 rounded-sm shadow-sm flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono tracking-widest uppercase text-muted mb-1 flex items-center gap-2">
            <span>ALPACA PAPER TRADING</span>
            <span className="text-stone">·</span>
            <span>ACCOUNT LEDGER</span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl text-ink font-normal tracking-tight">
            Portfolio Holdings & Liquidity
          </h2>
          <p className="text-xs md:text-sm text-ink/70 mt-1 font-sans">
            Live balance, buying power, and active paper positions queried directly from Alpaca Markets.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-bone px-3 py-1.5 rounded-sm border border-stone text-xs font-mono text-ink">
            <span className="text-muted">STATUS:</span>{" "}
            <strong className="text-positive">{portfolio?.account_status || "UNKNOWN"}</strong>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={onRefresh}
            isLoading={isLoading}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Refresh Ledger
          </Button>
        </div>
      </section>

      {/* Loading State */}
      {isLoading && (
        <LoadingState
          message="Querying Alpaca paper account ledger..."
          subtext="Fetching cash balances, buying power calculations, and open equity positions."
        />
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          title="Portfolio Data Unavailable"
          message={error}
          onRetry={onRefresh}
        />
      )}

      {/* Portfolio Content */}
      {!isLoading && !error && portfolio && (
        <div className="space-y-8 animate-fade-in">
          {/* Key Metric Ledger Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-chalk">
              <span className="text-[11px] font-mono tracking-wider uppercase text-muted block mb-1">
                Portfolio Value
              </span>
              <span className="font-mono text-2xl font-bold text-ink tracking-tight">
                {formatCurrency(portfolio.portfolio_value, portfolio.currency)}
              </span>
              <span className="text-[11px] text-muted font-sans block mt-1">
                Total equity under management
              </span>
            </Card>

            <Card className="bg-chalk">
              <span className="text-[11px] font-mono tracking-wider uppercase text-muted block mb-1">
                Cash Balance
              </span>
              <span className="font-mono text-2xl font-semibold text-ink tracking-tight">
                {formatCurrency(portfolio.cash, portfolio.currency)}
              </span>
              <span className="text-[11px] text-muted font-sans block mt-1">
                Settled unallocated funds
              </span>
            </Card>

            <Card className="bg-chalk">
              <span className="text-[11px] font-mono tracking-wider uppercase text-muted block mb-1">
                Buying Power
              </span>
              <span className="font-mono text-2xl font-semibold text-ink tracking-tight">
                {formatCurrency(portfolio.buying_power, portfolio.currency)}
              </span>
              <span className="text-[11px] text-muted font-sans block mt-1">
                Standard paper margin limit
              </span>
            </Card>

            <Card className="bg-chalk">
              <span className="text-[11px] font-mono tracking-wider uppercase text-muted block mb-1">
                Active Positions
              </span>
              <span className="font-mono text-2xl font-semibold text-ink tracking-tight">
                {portfolio.positions?.length || 0}
              </span>
              <span className="text-[11px] text-muted font-sans block mt-1">
                Open equity allocations
              </span>
            </Card>
          </div>

          {/* Positions Table */}
          <Card
            title="Open Portfolio Positions"
            subtitle="Verified equity holdings in paper broker account"
            badge={
              <Badge variant="neutral" size="sm">
                {portfolio.positions?.length || 0} POSITIONS
              </Badge>
            }
          >
            {portfolio.positions && portfolio.positions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-bone text-muted border-b border-stone text-[10px] uppercase tracking-wider">
                    <tr>
                      <th className="py-2.5 px-3">Asset</th>
                      <th className="py-2.5 px-3 text-right">Shares</th>
                      <th className="py-2.5 px-3 text-right">Avg Entry</th>
                      <th className="py-2.5 px-3 text-right">Current Price</th>
                      <th className="py-2.5 px-3 text-right">Market Value</th>
                      <th className="py-2.5 px-3 text-right">Unrealized P/L</th>
                      <th className="py-2.5 px-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone/60 bg-chalk">
                    {portfolio.positions.map((pos) => {
                      const pl = pos.unrealized_pl ?? 0;
                      const isPositive = pl > 0;
                      const isNegative = pl < 0;

                      return (
                        <tr key={pos.symbol} className="hover:bg-bone/40 transition-colors">
                          <td className="py-3 px-3">
                            <span className="font-bold text-ink text-sm block">
                              {pos.symbol}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right font-medium text-ink">
                            {formatNumber(pos.qty, 0)}
                          </td>
                          <td className="py-3 px-3 text-right text-muted">
                            {formatCurrency(pos.avg_entry_price)}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-ink">
                            {formatCurrency(pos.current_price)}
                          </td>
                          <td className="py-3 px-3 text-right font-semibold text-ink">
                            {formatCurrency(pos.market_value)}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <span
                              className={`font-semibold ${
                                isPositive
                                  ? "text-positive"
                                  : isNegative
                                  ? "text-oxide"
                                  : "text-muted"
                              }`}
                            >
                              {formatCurrency(pos.unrealized_pl)} (
                              {formatPercentage(pos.unrealized_plpc)})
                            </span>
                          </td>
                          <td className="py-3 px-3 text-center">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onSelectTicker(pos.symbol)}
                              className="text-[11px] text-muted hover:text-ink font-sans"
                            >
                              Research
                              <ArrowUpRight className="w-3 h-3 ml-0.5" />
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                title="No Open Positions"
                description="Your paper trading account holds 100% cash with no active equity allocations."
                icon={<Briefcase className="w-4 h-4 stroke-[1.5]" />}
              />
            )}

            <div className="mt-4 pt-3 border-t border-stone/60 flex items-center justify-between text-[11px] font-mono text-muted">
              <span>Timestamp: {formatDateTime(portfolio.timestamp)}</span>
              <span>Account Currency: {portfolio.currency}</span>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
