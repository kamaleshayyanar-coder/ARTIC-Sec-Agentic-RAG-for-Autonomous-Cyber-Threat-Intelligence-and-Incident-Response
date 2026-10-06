"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Play,
  Pause,
  Filter,
  Shield,
  ExternalLink,
  ChevronRight,
  Radio,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAlerts } from "@/hooks/useAlerts";
import { formatTimestamp, formatRiskScore, severityColor, truncate } from "@/lib/utils";

export function AlertFeed() {
  const { alerts, isPaused, togglePause, severityFilter, setSeverityFilter, updateAlertStatus } = useAlerts();
  const [selectedAlert, setSelectedAlert] = useState<any>(null);

  const severities = ["all", "critical", "high", "medium", "low"];

  const filteredAlerts = alerts.filter((a) => {
    if (!severityFilter || severityFilter === "all") return true;
    return a.severity.toLowerCase() === severityFilter.toLowerCase();
  });

  return (
    <Card className="flex flex-col h-[520px] border-slate-800 bg-night-900/80">
      <CardHeader className="p-4 pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-rose-500/10 border border-rose-500/20">
            <Radio className="h-4 w-4 text-rose-400 animate-pulse" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Real-Time Alert Feed
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {filteredAlerts.length} events
              </span>
            </CardTitle>
            <p className="text-[11px] text-slate-400">Streaming live IDS inference & network anomalies</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Pause / Resume button */}
          <Button
            variant="outline"
            size="sm"
            onClick={togglePause}
            className={`h-7 px-2.5 text-xs gap-1.5 ${
              isPaused
                ? "border-amber-500/40 bg-amber-500/10 text-amber-300 hover:bg-amber-500/20"
                : "border-slate-700 hover:bg-slate-800 text-slate-300"
            }`}
          >
            {isPaused ? <Play className="h-3 w-3" /> : <Pause className="h-3 w-3" />}
            {isPaused ? "Resume" : "Pause"}
          </Button>

          {/* Severity Filter Pills */}
          <div className="hidden sm:flex items-center gap-1 bg-night-950 p-0.5 rounded-lg border border-slate-800">
            {severities.map((sev) => {
              const active = (severityFilter || "all").toLowerCase() === sev;
              return (
                <button
                  key={sev}
                  onClick={() => setSeverityFilter(sev === "all" ? null : sev)}
                  className={`px-2 py-0.5 text-[10px] uppercase font-semibold rounded capitalize transition-all ${
                    active
                      ? "bg-slate-800 text-sky-400 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {sev}
                </button>
              );
            })}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 flex-1 overflow-y-auto divide-y divide-slate-800/60 font-mono text-xs">
        {filteredAlerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12 text-slate-500 text-xs">
            <Shield className="h-8 w-8 text-slate-600 mb-2 opacity-60" />
            <span>No incoming alerts matching filter criteria.</span>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const colors = severityColor(alert.severity);
            const isHigh = alert.risk_score >= 0.7;

            return (
              <div
                key={alert.id}
                className="p-3.5 hover:bg-slate-800/30 transition-colors flex items-center justify-between group cursor-pointer"
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={`w-1.5 h-8 rounded-full shrink-0 ${
                      alert.severity === "critical"
                        ? "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]"
                        : alert.severity === "high"
                        ? "bg-amber-500"
                        : alert.severity === "medium"
                        ? "bg-yellow-500"
                        : "bg-slate-600"
                    }`}
                  />

                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200 tracking-wide">{alert.type}</span>
                      <span
                        className={`text-[10px] uppercase px-1.5 py-0.2 rounded border font-sans font-bold ${colors.badge}`}
                      >
                        {alert.severity}
                      </span>
                      {alert.mitre_technique && (
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-950/60 border border-sky-800/50 text-sky-300 font-sans">
                          {alert.mitre_technique}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400">
                      <span className="text-slate-300">{alert.src_ip}</span>
                      <ArrowRight className="h-3 w-3 text-slate-600" />
                      <span className="text-slate-400">{alert.dst_ip}</span>
                      <span className="text-slate-600">•</span>
                      <span className="text-slate-500 font-sans">{formatTimestamp(alert.timestamp)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <div className="text-right">
                    <div
                      className={`text-xs font-bold ${
                        isHigh ? "text-rose-400" : "text-slate-300"
                      }`}
                    >
                      {formatRiskScore(alert.risk_score)}
                    </div>
                    <div className="text-[10px] text-slate-500 uppercase font-sans">Risk</div>
                  </div>

                  <Link
                    href={alert.incident_id ? `/incidents/${alert.incident_id}` : `/alerts?id=${alert.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="p-1 rounded text-slate-500 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </CardContent>
    </Card>
  );
}
