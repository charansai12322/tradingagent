"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Masthead, ActiveTab } from "@/components/layout/Masthead";
import { OverviewSection } from "@/features/overview/OverviewSection";
import { AnalysisSection } from "@/features/analysis/AnalysisSection";
import { PortfolioSection } from "@/features/portfolio/PortfolioSection";
import { OrderReviewSection } from "@/features/orders/OrderReviewSection";
import { OrderApprovalModal } from "@/features/orders/OrderApprovalModal";
import { SystemStatusSection } from "@/features/system-status/SystemStatusSection";
import { tradingApi } from "@/lib/api";
import {
  HealthResponse,
  PortfolioResponse,
  AnalysisResponse,
  ProposedOrder,
  OrderExecutionResult,
} from "@/types/trading";

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("overview");

  // Health Diagnostic State
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  // Portfolio State
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState<boolean>(false);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);

  // Market Analysis State
  const [currentSymbol, setCurrentSymbol] = useState<string>("AAPL");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Session Collections
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisResponse[]>([]);
  const [proposals, setProposals] = useState<ProposedOrder[]>([]);

  // Order Approval Modal State
  const [selectedProposal, setSelectedProposal] = useState<ProposedOrder | null>(null);
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);

  // Fetch Health
  const loadHealth = useCallback(async () => {
    try {
      setHealthLoading(true);
      const data = await tradingApi.getHealth();
      setHealth(data);
      setHealthError(null);
    } catch (err) {
      setHealthError(err instanceof Error ? err.message : "Backend service unreachable");
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // Fetch Portfolio
  const loadPortfolio = useCallback(async () => {
    try {
      setPortfolioLoading(true);
      const data = await tradingApi.getPortfolio();
      setPortfolio(data);
      setPortfolioError(null);
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : "Failed to load paper portfolio");
    } finally {
      setPortfolioLoading(false);
    }
  }, []);

  // Initial Load
  useEffect(() => {
    loadHealth();
    loadPortfolio();
  }, [loadHealth, loadPortfolio]);

  // Run Analysis
  const handleRunAnalysis = async (symbol: string) => {
    setAnalysisLoading(true);
    setAnalysisError(null);
    try {
      const result = await tradingApi.analyzeStock(symbol);
      setAnalysisResult(result);
      setCurrentSymbol(symbol);

      // Add to recent analyses session history (deduplicating by symbol)
      setRecentAnalyses((prev) => [
        result,
        ...prev.filter((p) => p.symbol !== result.symbol),
      ].slice(0, 8));

      // If a proposed order was generated, add it to proposals
      if (result.proposed_order) {
        setProposals((prev) => [
          result.proposed_order!,
          ...prev.filter((p) => p.proposal_id !== result.proposed_order!.proposal_id),
        ]);
      }
    } catch (err) {
      setAnalysisError(err instanceof Error ? err.message : "Analysis request failed");
      setAnalysisResult(null);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Open Approval Modal
  const handleOpenOrderModal = (proposal: ProposedOrder) => {
    setSelectedProposal(proposal);
    setIsOrderModalOpen(true);
  };

  // Approve Order Handler
  const handleApproveOrder = async (proposalId: string): Promise<OrderExecutionResult> => {
    const result = await tradingApi.approveOrder(proposalId, true);
    // Refresh portfolio after attempted action
    loadPortfolio();
    return result;
  };

  return (
    <div className="min-h-screen bg-bone flex flex-col font-sans text-ink">
      {/* Editorial Masthead */}
      <Masthead
        activeTab={activeTab}
        onTabChange={setActiveTab}
        health={health}
        healthLoading={healthLoading}
        healthError={healthError}
      />

      {/* Main Workspace Canvas */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-8 py-8">
        {activeTab === "overview" && (
          <OverviewSection
            health={health}
            healthLoading={healthLoading}
            healthError={healthError}
            portfolio={portfolio}
            portfolioLoading={portfolioLoading}
            portfolioError={portfolioError}
            recentAnalyses={recentAnalyses}
            onSelectTicker={(sym) => setCurrentSymbol(sym)}
            onNavigateTab={(tab) => setActiveTab(tab)}
            onRefreshAll={() => {
              loadHealth();
              loadPortfolio();
            }}
          />
        )}

        {activeTab === "analysis" && (
          <AnalysisSection
            currentSymbol={currentSymbol}
            onSymbolChange={setCurrentSymbol}
            onRunAnalysis={handleRunAnalysis}
            analysisResult={analysisResult}
            isLoading={analysisLoading}
            error={analysisError}
            onOpenOrderModal={handleOpenOrderModal}
          />
        )}

        {activeTab === "portfolio" && (
          <PortfolioSection
            portfolio={portfolio}
            isLoading={portfolioLoading}
            error={portfolioError}
            onRefresh={loadPortfolio}
            onSelectTicker={(sym) => {
              setCurrentSymbol(sym);
              setActiveTab("analysis");
              handleRunAnalysis(sym);
            }}
          />
        )}

        {activeTab === "orders" && (
          <OrderReviewSection
            proposals={proposals}
            tradingEnabled={health?.trading_enabled ?? false}
            orderApprovalRequired={health?.order_approval_required ?? true}
            onOpenApprovalModal={handleOpenOrderModal}
            onNavigateToAnalysis={() => setActiveTab("analysis")}
          />
        )}

        {activeTab === "status" && (
          <SystemStatusSection
            health={health}
            isLoading={healthLoading}
            error={healthError}
            onRefresh={loadHealth}
          />
        )}
      </main>

      {/* Order Approval Modal */}
      <OrderApprovalModal
        isOpen={isOrderModalOpen}
        onClose={() => setIsOrderModalOpen(false)}
        proposal={selectedProposal}
        tradingEnabled={health?.trading_enabled ?? false}
        onApprove={handleApproveOrder}
      />

      {/* Editorial Colophon / Footer */}
      <footer className="border-t border-stone bg-bone py-8 px-4 md:px-8 text-xs font-sans text-muted">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex items-baseline gap-2 mb-1">
              <span className="font-serif text-lg text-ink font-normal">chaai.</span>
              <span className="font-mono text-[11px] text-muted">
                Clarity over constant activity.
              </span>
            </div>
            <p className="text-[11px] text-muted max-w-xl leading-relaxed">
              CHAAI is an independent financial intelligence workstation combining Gemini reasoning, TwelveData analytics, Finnhub sentiment, and Alpaca paper sandboxing. Non-advisory research tool. Simulated paper execution only.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 text-[11px] font-mono">
            <span className="bg-chalk px-2.5 py-1 rounded-sm border border-stone">
              TRADING_ENABLED = {health?.trading_enabled ? "true" : "false"}
            </span>
            <span className="bg-chalk px-2.5 py-1 rounded-sm border border-stone">
              MODE = {health?.trading_mode?.toUpperCase() || "PAPER"}
            </span>
            <span className="text-muted">© 2026 chaai.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
