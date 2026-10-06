"use client";

import React from "react";
import { ShieldAlert, Zap, Timer, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useMetrics } from "@/hooks/useMetrics";

export function MetricsCards() {
  const { metrics, loading } = useMetrics(5000);

  const cards = [
    {
      title: "Total Alerts Processed",
      value: metrics.total_alerts.toLocaleString(),
      subtitle: "CIC-IDS2017 & Live Streams",
      icon: ShieldAlert,
      color: "text-sky-400",
      bg: "bg-sky-500/10 border-sky-500/20",
      trend: "+12.4% / hr",
    },
    {
      title: "Critical & High Risk",
      value: metrics.high_risk_count.toLocaleString(),
      subtitle: "Requires Immediate Mitigation",
      icon: AlertTriangle,
      color: "text-rose-400",
      bg: "bg-rose-500/10 border-rose-500/20",
      trend: `${metrics.total_alerts > 0 ? Math.round((metrics.high_risk_count / metrics.total_alerts) * 100) : 0}% of traffic`,
      highlight: true,
    },
    {
      title: "Mean Time To Detect (MTTD)",
      value: `${metrics.mttd_seconds.toFixed(1)}s`,
      subtitle: "Real-time ONNX + Hybrid RAG",
      icon: Zap,
      color: "text-amber-400",
      bg: "bg-amber-500/10 border-amber-500/20",
      trend: "Target: <15s",
    },
    {
      title: "Autonomous Resolution",
      value: `${(metrics.auto_resolution_rate * 100).toFixed(1)}%`,
      subtitle: `MTTR: ${metrics.mttr_seconds.toFixed(0)}s`,
      icon: CheckCircle2,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10 border-emerald-500/20",
      trend: "Agent Containment",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card
            key={idx}
            className={`relative overflow-hidden border transition-all duration-200 hover:border-slate-700 ${
              card.highlight ? "border-rose-900/40 bg-rose-950/10" : "border-slate-800 bg-night-900/70"
            }`}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{card.title}</span>
                <div className={`p-2 rounded-lg border ${card.bg}`}>
                  <Icon className={`h-4 w-4 ${card.color}`} />
                </div>
              </div>

              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold font-mono tracking-tight text-slate-100">
                  {loading ? "..." : card.value}
                </span>
                <span className="text-[11px] font-mono text-slate-400">{card.trend}</span>
              </div>

              <p className="mt-1 text-[11px] text-slate-400 truncate">{card.subtitle}</p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
