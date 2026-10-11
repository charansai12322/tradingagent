"use client";

import React from "react";
import { ShieldAlert, Activity, CheckCircle2, AlertCircle } from "lucide-react";
import { HealthResponse } from "@/types/trading";

export type ActiveTab = "overview" | "analysis" | "portfolio" | "orders" | "status";

export interface MastheadProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  healthError: string | null;
}

export const Masthead: React.FC<MastheadProps> = ({
  activeTab,
  onTabChange,
  health,
  healthLoading,
  healthError,
}) => {
  const currentDate = new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date());

  const navItems: { id: ActiveTab; label: string; number: string }[] = [
    { id: "overview", label: "Overview", number: "01" },
    { id: "analysis", label: "Market Research", number: "02" },
    { id: "portfolio", label: "Portfolio", number: "03" },
    { id: "orders", label: "Order Governance", number: "04" },
    { id: "status", label: "System Health", number: "05" },
  ];

  return (
    <header className="border-b border-stone bg-bone sticky top-0 z-40">
      {/* Top Utility Band */}
      <div className="border-b border-stone/60 px-4 md:px-8 py-1.5 flex items-center justify-between text-[11px] font-mono text-muted tracking-tight">
        <div className="flex items-center gap-3">
          <span className="uppercase tracking-wider">CHAAI TRADING WORKSTATION</span>
          <span className="text-stone">/</span>
          <span>{currentDate} UTC</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Paper Safety Badge */}
          <div className="flex items-center gap-1.5 bg-chalk px-2 py-0.5 rounded-sm border border-stone/80 text-[10px] text-ink">
            <ShieldAlert className="w-3 h-3 text-oxide" />
            <span className="font-semibold tracking-wider">PAPER MODE</span>
            <span className="text-stone">·</span>
            <span className="text-muted">EXECUTION DISABLED</span>
          </div>

          {/* Backend Connectivity Status */}
          <div
            onClick={() => onTabChange("status")}
            className="cursor-pointer flex items-center gap-1.5 hover:text-ink transition-colors"
            title="Click to view detailed system diagnostics"
          >
            {healthLoading ? (
              <span className="w-2 h-2 rounded-full bg-warning animate-pulse" />
            ) : health ? (
              <span className="w-2 h-2 rounded-full bg-positive" />
            ) : (
              <span className="w-2 h-2 rounded-full bg-oxide" />
            )}
            <span className="hidden sm:inline">
              {healthLoading
                ? "Connecting..."
                : health
                ? "API Online"
                : "API Offline"}
            </span>
          </div>
        </div>
      </div>

      {/* Main Editorial Masthead */}
      <div className="px-4 md:px-8 py-5 md:py-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-baseline gap-2">
            <h1 className="font-serif text-3xl md:text-4xl text-ink font-normal tracking-tight">
              chaai<span className="text-oxide">.</span>
            </h1>
            <span className="text-xs font-mono tracking-widest uppercase text-muted">
              v0.3.0
            </span>
          </div>
          <p className="font-sans text-xs md:text-sm text-muted mt-1 tracking-normal font-normal">
            Clarity over constant activity. AI-driven technical synthesis & disciplined execution.
          </p>
        </div>

        {/* Desktop Editorial Navigation */}
        <nav
          aria-label="Main Navigation"
          className="flex items-center gap-1 sm:gap-2 overflow-x-auto pb-1 md:pb-0 scrollbar-none"
        >
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`group flex items-baseline gap-1.5 px-3 py-1.5 rounded-sm text-xs md:text-sm font-sans transition-all duration-150 whitespace-nowrap focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ink ${
                  isActive
                    ? "bg-chalk text-ink font-semibold border border-stone shadow-sm"
                    : "text-muted hover:text-ink hover:bg-stone/20"
                }`}
              >
                <span
                  className={`text-[10px] font-mono transition-colors ${
                    isActive ? "text-oxide font-medium" : "text-muted/60 group-hover:text-muted"
                  }`}
                >
                  {item.number}
                </span>
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
