"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { BarChart3 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useMetrics } from "@/hooks/useMetrics";

export function AlertVolumeChart({ height = 280 }: { height?: number }) {
  const { hourly, loading } = useMetrics(10000);

  const formattedData = (hourly || []).map((p) => {
    const timeLabel = p.hour ? p.hour.split("T")[1]?.substring(0, 5) || p.hour : "";
    return {
      time: timeLabel,
      total: p.count,
      highRisk: p.high_risk,
    };
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border border-slate-700 bg-night-950 p-2.5 shadow-xl text-xs font-mono">
          <div className="text-slate-400 mb-1">Time: {label} UTC</div>
          <div className="text-sky-400 flex items-center justify-between gap-4">
            <span>Total Alerts:</span>
            <span className="font-bold">{payload[0]?.value}</span>
          </div>
          <div className="text-rose-400 flex items-center justify-between gap-4 mt-0.5">
            <span>High Risk:</span>
            <span className="font-bold">{payload[1]?.value}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="flex flex-col border-slate-800 bg-night-900/80">
      <CardHeader className="p-4 pb-2 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-sky-500/10 border border-sky-500/20">
            <BarChart3 className="h-4 w-4 text-sky-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Alert Ingestion Velocity
            </CardTitle>
            <p className="text-[11px] text-slate-400">24-hour event timeline (Total vs High Risk)</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284c7" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#e11d48" stopOpacity={0.5} />
                <stop offset="95%" stopColor="#e11d48" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} />
            <YAxis stroke="#64748b" tick={{ fontSize: 10, fill: "#64748b" }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
              formatter={(value) => <span className="text-slate-300 capitalize">{value}</span>}
            />

            <Area
              type="monotone"
              dataKey="total"
              name="Total Alerts"
              stroke="#38bdf8"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#totalGrad)"
            />
            <Area
              type="monotone"
              dataKey="highRisk"
              name="High Risk"
              stroke="#f43f5e"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#highGrad)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
