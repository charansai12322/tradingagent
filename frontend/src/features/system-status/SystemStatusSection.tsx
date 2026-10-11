"use client";

import React from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Server,
  Cpu,
  LineChart,
  Newspaper,
  ShieldCheck,
  Eye,
  Lock,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { HealthResponse } from "@/types/trading";

export interface SystemStatusSectionProps {
  health: HealthResponse | null;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const SystemStatusSection: React.FC<SystemStatusSectionProps> = ({
  health,
  isLoading,
  error,
  onRefresh,
}) => {
  const providers = [
    {
      name: "Google Gemini",
      category: "AI Reasoning & Synthesis",
      isConfigured: health?.providers?.gemini ?? false,
      model: "gemini-2.5-flash",
      description: "Generates structured market recommendations, rationales, and risk summaries.",
      icon: <Cpu className="w-4 h-4 text-ink" />,
    },
    {
      name: "TwelveData",
      category: "Real-Time & Historical Market Data",
      isConfigured: health?.providers?.twelvedata ?? false,
      model: "/price & /time_series",
      description: "Supplies current price quotes and historical closing prices for RSI and SMA indicators.",
      icon: <LineChart className="w-4 h-4 text-ink" />,
    },
    {
      name: "Finnhub",
      category: "Company News & Sentiment",
      isConfigured: health?.providers?.finnhub ?? false,
      model: "/company-news",
      description: "Feeds recent company news headlines with injection sanitization.",
      icon: <Newspaper className="w-4 h-4 text-ink" />,
    },
    {
      name: "Alpaca Markets",
      category: "Paper Brokerage & Portfolio Ledger",
      isConfigured: health?.providers?.alpaca ?? false,
      model: "paper-api.alpaca.markets",
      description: "Simulated paper trading sandbox with read-only portfolio queries.",
      icon: <ShieldCheck className="w-4 h-4 text-ink" />,
    },
    {
      name: "LangSmith",
      category: "LLM Observability & Tracing",
      isConfigured: health?.providers?.langsmith ?? false,
      model: "api.smith.langchain.com",
      description: "Optional execution tracing for prompt inspection and latency telemetry.",
      icon: <Eye className="w-4 h-4 text-ink" />,
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* System Diagnostic Masthead */}
      <section className="bg-chalk border border-stone p-6 rounded-sm shadow-sm flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="text-[11px] font-mono tracking-widest uppercase text-muted mb-1 flex items-center gap-2">
            <span>HEALTH & DIAGNOSTICS</span>
            <span className="text-stone">·</span>
            <span>READINESS REPORT</span>
          </div>
          <h2 className="font-serif text-2xl md:text-3xl text-ink font-normal tracking-tight">
            Infrastructure & Integration Health
          </h2>
          <p className="text-xs md:text-sm text-ink/70 mt-1 font-sans">
            Truthful, backend-derived connectivity status for all external APIs and safety mechanisms.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={onRefresh}
          isLoading={isLoading}
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" />
          Poll Health Endpoint
        </Button>
      </section>

      {/* Backend API Service Health Banner */}
      <Card
        title="FastAPI Backend Gateway"
        subtitle={`Base URL: ${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"}`}
        badge={
          isLoading ? (
            <Badge variant="warning" size="sm">Polling</Badge>
          ) : health ? (
            <Badge variant="positive" size="sm">Online (HTTP 200)</Badge>
          ) : (
            <Badge variant="oxide" size="sm">Unreachable</Badge>
          )
        }
      >
        {error ? (
          <div className="p-4 bg-[#A34F3F]/10 border border-oxide/40 rounded-sm text-xs font-sans text-oxide">
            <strong>Connection Error:</strong> {error}
            <p className="text-[11px] text-muted mt-1 font-sans">
              Ensure the FastAPI service is active via <code className="bg-bone px-1 py-0.5 rounded font-mono">uvicorn app.main:app --reload</code> in <code className="bg-bone px-1 py-0.5 rounded font-mono">backend/</code>.
            </p>
          </div>
        ) : health ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
              <span className="text-muted block text-[10px] uppercase">Service Status</span>
              <span className="font-bold text-positive text-sm uppercase">{health.status}</span>
            </div>
            <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
              <span className="text-muted block text-[10px] uppercase">Environment</span>
              <span className="font-semibold text-ink text-sm">{health.app_env}</span>
            </div>
            <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
              <span className="text-muted block text-[10px] uppercase">Trading Mode</span>
              <span className="font-semibold text-ink text-sm uppercase">{health.trading_mode}</span>
            </div>
            <div className="p-3 bg-bone/40 rounded-sm border border-stone/60">
              <span className="text-muted block text-[10px] uppercase">Execution Enabled</span>
              <span className={`font-bold text-sm ${health.trading_enabled ? "text-oxide" : "text-positive"}`}>
                {health.trading_enabled ? "ENABLED" : "FALSE (SAFE)"}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-xs text-muted font-sans py-2">
            Waiting for backend service response...
          </p>
        )}
      </Card>

      {/* Provider Connectivity Grid */}
      <Card
        title="External Provider Integrations"
        subtitle="Individual API status reported by backend /health inspection"
        badge={
          <Badge variant="neutral" size="sm">
            {health?.providers
              ? Object.values(health.providers).filter(Boolean).length + " / 5 Active"
              : "0 Active"}
          </Badge>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map((p) => (
            <div
              key={p.name}
              className="p-4 bg-bone/30 rounded-sm border border-stone/70 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-sm bg-chalk border border-stone flex items-center justify-center">
                      {p.icon}
                    </div>
                    <div>
                      <h4 className="font-mono text-sm font-bold text-ink">
                        {p.name}
                      </h4>
                      <span className="text-[10px] font-mono text-muted uppercase">
                        {p.category}
                      </span>
                    </div>
                  </div>

                  <Badge
                    variant={p.isConfigured ? "positive" : "muted"}
                    size="sm"
                  >
                    {p.isConfigured ? "Connected" : "Not Configured"}
                  </Badge>
                </div>

                <p className="text-xs text-ink/75 font-sans leading-relaxed mt-2">
                  {p.description}
                </p>
              </div>

              <div className="mt-4 pt-2 border-t border-stone/50 flex items-center justify-between text-[10px] font-mono text-muted">
                <span>Endpoint / Model:</span>
                <span className="font-semibold text-ink">{p.model}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};
