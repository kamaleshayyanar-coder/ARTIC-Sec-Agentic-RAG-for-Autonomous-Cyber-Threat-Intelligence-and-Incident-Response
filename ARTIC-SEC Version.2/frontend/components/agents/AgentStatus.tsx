"use client";

import React, { useEffect, useState } from "react";
import { Bot, Shield, Eye, Cpu, FileText, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getAgentStatus, type AgentInfo } from "@/lib/api";

const AGENT_ICONS: Record<string, any> = {
  recon: Eye,
  analysis: Cpu,
  response: Shield,
  guardrail: AlertCircle,
  report: FileText,
};

export function AgentStatus() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await getAgentStatus();
      setAgents(res.agents || []);
    } catch (err) {
      console.warn("Agent status fetch failed", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="border-slate-800 bg-night-900/80">
      <CardHeader className="p-4 pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-sky-500/10 border border-sky-500/20">
            <Bot className="h-4 w-4 text-sky-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              LangGraph Agent Swarm Health
            </CardTitle>
            <p className="text-[11px] text-slate-400">Autonomous multi-agent orchestration states</p>
          </div>
        </div>

        <button
          onClick={fetchStatus}
          className="p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Refresh agent states"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
        </button>
      </CardHeader>

      <CardContent className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {agents.map((agent) => {
            const Icon = AGENT_ICONS[agent.id] || Bot;
            const isGuardrail = agent.id === "guardrail";

            return (
              <div
                key={agent.id}
                className="p-3 rounded-lg border border-slate-800 bg-night-950/70 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="p-1.5 rounded-md bg-slate-800/80 text-sky-400 border border-slate-700/60">
                      <Icon className="h-4 w-4" />
                    </div>
                    <Badge
                      variant="outline"
                      className="text-[10px] uppercase font-mono border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
                    >
                      {agent.status}
                    </Badge>
                  </div>

                  <div className="font-semibold text-xs text-slate-200">{agent.name}</div>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                    {agent.description}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span>Task: {agent.current_task || "idle"}</span>
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
