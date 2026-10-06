"use client";

import React from "react";
import { Server, Wifi, Cpu, BookOpen, ExternalLink, ShieldCheck } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useMetrics } from "@/hooks/useMetrics";

export function Footer() {
  const { connected } = useWebSocket();
  const { metrics } = useMetrics(10000);

  return (
    <footer className="h-10 border-t border-slate-800/80 bg-night-950 px-6 flex items-center justify-between text-[11px] text-slate-400 select-none">
      <div className="flex items-center gap-6">
        <span className="flex items-center gap-1.5 font-mono text-slate-300">
          <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
          ARTIC-Sec Enterprise SOC v1.0.0
        </span>
        <div className="hidden sm:flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <Server className="h-3.5 w-3.5 text-slate-500" />
            Backend: <span className="text-emerald-400 font-mono">FastAPI</span>
          </span>
          <span className="flex items-center gap-1.5">
            <Wifi className="h-3.5 w-3.5 text-slate-500" />
            Live WS:{" "}
            <span className={connected ? "text-emerald-400 font-mono" : "text-amber-400 font-mono"}>
              {connected ? `${metrics.websocket_clients || 1} active` : "disconnected"}
            </span>
          </span>
          <span className="flex items-center gap-1.5">
            <Cpu className="h-3.5 w-3.5 text-slate-500" />
            Model: <span className="text-sky-400 font-mono">Llama 3.2 + XGBoost</span>
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1 hover:text-sky-400 transition-colors"
        >
          <BookOpen className="h-3 w-3" />
          <span>Swagger API</span>
          <ExternalLink className="h-2.5 w-2.5 opacity-60" />
        </a>
      </div>
    </footer>
  );
}
