"use client";

import React from "react";
import { MetricsCards } from "@/components/dashboard/MetricsCards";
import { AlertFeed } from "@/components/dashboard/AlertFeed";
import { AttackGraph } from "@/components/dashboard/AttackGraph";
import { AIInsights } from "@/components/dashboard/AIInsights";
import { AlertVolumeChart } from "@/components/dashboard/AlertVolumeChart";
import { ThreatMap } from "@/components/dashboard/ThreatMap";
import { AgentStatus } from "@/components/agents/AgentStatus";

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-8">
      {/* KPI Metrics */}
      <MetricsCards />

      {/* Main Grid: Alert Stream & Attack Graph */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6 xl:col-span-5">
          <AlertFeed />
        </div>
        <div className="lg:col-span-6 xl:col-span-7">
          <AttackGraph />
        </div>
      </div>

      {/* Secondary Grid: SSE AI Insights & Volume Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <AIInsights />
        </div>
        <div className="lg:col-span-6">
          <AlertVolumeChart />
        </div>
      </div>

      {/* Geo Threat Telemetry */}
      <div className="grid grid-cols-1 gap-6">
        <ThreatMap />
      </div>

      {/* Multi-Agent Orchestrator Health */}
      <div>
        <AgentStatus />
      </div>
    </div>
  );
}
