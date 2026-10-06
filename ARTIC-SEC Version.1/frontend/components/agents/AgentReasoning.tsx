"use client";

import React, { useState } from "react";
import {
  GitCommit,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Cpu,
  Shield,
  Eye,
  FileText,
  Play,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { runIncidentAgents } from "@/lib/api";

interface StepItem {
  agent: string;
  action: string;
  output?: any;
  timestamp?: string;
  status?: string;
}

interface AgentReasoningProps {
  incidentId: number;
  initialSteps?: StepItem[];
  onAgentsCompleted?: () => void;
}

export function AgentReasoning({ incidentId, initialSteps = [], onAgentsCompleted }: AgentReasoningProps) {
  const [steps, setSteps] = useState<StepItem[]>(initialSteps);
  const [isRunning, setIsRunning] = useState(false);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const handleRunAgents = async () => {
    setIsRunning(true);
    try {
      const res = await runIncidentAgents(incidentId);
      if (res.steps) {
        setSteps(res.steps);
      }
      if (onAgentsCompleted) {
        onAgentsCompleted();
      }
    } catch (err) {
      console.error("Agent execution failed", err);
    } finally {
      setIsRunning(false);
    }
  };

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  const getAgentIcon = (agent: string) => {
    const a = agent.toLowerCase();
    if (a.includes("recon")) return Eye;
    if (a.includes("analysis")) return Cpu;
    if (a.includes("guardrail")) return AlertTriangle;
    if (a.includes("response")) return Shield;
    if (a.includes("report")) return FileText;
    return GitCommit;
  };

  return (
    <Card className="border-slate-800 bg-night-900/80">
      <CardHeader className="p-4 pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-purple-500/10 border border-purple-500/20">
            <GitCommit className="h-4 w-4 text-purple-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Multi-Agent Reasoning Trace
            </CardTitle>
            <p className="text-[11px] text-slate-400">Step-by-step audit of autonomous incident decisioning</p>
          </div>
        </div>

        <Button
          size="sm"
          onClick={handleRunAgents}
          disabled={isRunning}
          className="h-8 gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs"
        >
          <Play className={`h-3.5 w-3.5 ${isRunning ? "animate-spin" : ""}`} />
          {isRunning ? "Running Agent Swarm..." : "Invoke Agent Swarm"}
        </Button>
      </CardHeader>

      <CardContent className="p-4">
        {steps.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs font-mono">
            No agent trace recorded yet. Click &quot;Invoke Agent Swarm&quot; to execute autonomous response workflow.
          </div>
        ) : (
          <div className="relative border-l border-slate-800 ml-4 space-y-4 font-mono">
            {steps.map((step, idx) => {
              const Icon = getAgentIcon(step.agent);
              const isExpanded = expandedIndex === idx;

              return (
                <div key={idx} className="relative pl-6">
                  {/* Timeline bullet icon */}
                  <span className="absolute -left-3 top-1 flex h-6 w-6 items-center justify-center rounded-full border border-slate-700 bg-night-950 text-sky-400">
                    <Icon className="h-3 w-3" />
                  </span>

                  <div className="rounded-lg border border-slate-800 bg-night-950/70 p-3 hover:border-slate-700 transition-all">
                    <div
                      className="flex items-center justify-between cursor-pointer select-none"
                      onClick={() => toggleExpand(idx)}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-sky-400">{step.agent}</span>
                        <span className="text-xs text-slate-300 font-sans font-medium">
                          {step.action}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className="text-[10px] uppercase border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
                        >
                          Completed
                        </Badge>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 text-slate-400" />
                        ) : (
                          <ChevronDown className="h-4 w-4 text-slate-400" />
                        )}
                      </div>
                    </div>

                    {isExpanded && step.output && (
                      <div className="mt-3 pt-3 border-t border-slate-800/80 text-[11px] text-slate-300">
                        <div className="text-slate-500 text-[10px] uppercase font-bold mb-1">
                          Output Payload:
                        </div>
                        <pre className="p-2.5 rounded bg-night-900 border border-slate-800 text-[10px] overflow-x-auto text-sky-200">
                          {typeof step.output === "object"
                            ? JSON.stringify(step.output, null, 2)
                            : String(step.output)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
