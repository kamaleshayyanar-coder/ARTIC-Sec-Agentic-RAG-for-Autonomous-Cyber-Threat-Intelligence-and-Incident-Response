"use client";

import React, { useState } from "react";
import { Share2, Filter, Layers, Info, ShieldAlert, Cpu } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { AttackGraph } from "@/components/dashboard/AttackGraph";
import { Badge } from "@/components/ui/badge";

export default function GraphPage() {
  const [selectedStage, setSelectedStage] = useState<string>("all");

  const STAGES = [
    { id: "all", label: "All Tactic Stages" },
    { id: "reconnaissance", label: "Reconnaissance (TA0043)" },
    { id: "discovery", label: "Discovery (TA0007)" },
    { id: "execution", label: "Execution (TA0002)" },
    { id: "lateral-movement", label: "Lateral Movement (TA0008)" },
    { id: "exfiltration", label: "Exfiltration (TA0010)" },
  ];

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Share2 className="h-5 w-5 text-amber-400" />
            MITRE ATT&CK Attack Graph
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Visualizing attacker telemetry, technique relationships, and enterprise asset blast radius.
          </p>
        </div>

        {/* Stage Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5 bg-night-900/80 p-1 rounded-lg border border-slate-800">
          {STAGES.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedStage(s.id)}
              className={`px-2.5 py-1 text-xs font-mono rounded-md transition-colors ${
                selectedStage === s.id
                  ? "bg-sky-600 text-white font-semibold shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Full-Screen Graph Card */}
      <div className="grid grid-cols-1 gap-6">
        <AttackGraph height={680} />
      </div>

      {/* Explanation Legend Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-night-900/60 p-4">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-xs font-mono mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500 shadow-[0_0_8px_#f43f5e]" />
            Attacker Nodes
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Represents external or compromised source IP addresses orchestrating malicious probes, scans, or exploitation attempts.
          </p>
        </Card>

        <Card className="border-slate-800 bg-night-900/60 p-4">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-xs font-mono mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_#f59e0b]" />
            Technique Nodes
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Correlated MITRE ATT&CK techniques (e.g., T1046 Network Service Discovery, T1190 Exploit Public-Facing Application).
          </p>
        </Card>

        <Card className="border-slate-800 bg-night-900/60 p-4">
          <div className="flex items-center gap-2 text-sky-400 font-bold text-xs font-mono mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400 shadow-[0_0_8px_#38bdf8]" />
            Tactic Categories
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            High-level adversary goals in the cyber kill-chain (Discovery, Initial Access, Lateral Movement, Impact).
          </p>
        </Card>

        <Card className="border-slate-800 bg-night-900/60 p-4">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs font-mono mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
            Internal Assets
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Target infrastructure, internal subnets, database clusters, and domain controllers targeted by adversary traffic.
          </p>
        </Card>
      </div>
    </div>
  );
}
