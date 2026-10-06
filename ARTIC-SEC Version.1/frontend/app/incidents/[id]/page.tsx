"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowLeft,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Server,
  Share2,
  Play,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AgentReasoning } from "@/components/agents/AgentReasoning";
import { AttackGraph } from "@/components/dashboard/AttackGraph";
import { getIncident, getIncidentReasoning, updateIncident, type IncidentItem } from "@/lib/api";
import { formatTimestamp, severityColor, formatRiskScore } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = Number(params.id);
  const { toast } = useToast();

  const [incident, setIncident] = useState<IncidentItem | null>(null);
  const [reasoningSteps, setReasoningSteps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadIncidentData = async () => {
    if (isNaN(incidentId)) return;
    setLoading(true);
    try {
      const [data, reasoning] = await Promise.all([
        getIncident(incidentId),
        getIncidentReasoning(incidentId).catch(() => ({ steps: [] })),
      ]);
      setIncident(data);
      setReasoningSteps(reasoning.steps || []);
    } catch (err: any) {
      toast({ title: "Failed to load incident", description: err.message, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidentData();
  }, [incidentId]);

  const handleStatusChange = async (newStatus: string) => {
    if (!incident) return;
    try {
      const updated = await updateIncident(incident.id, { status: newStatus });
      setIncident(updated);
      toast({ title: `Incident #${incident.id} marked as ${newStatus}`, type: "success" });
    } catch (err: any) {
      toast({ title: "Status update failed", description: err.message, type: "error" });
    }
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center font-mono text-xs text-slate-500">
        Loading Incident Case #{incidentId}...
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="flex flex-col items-center justify-center h-96 font-mono text-xs text-slate-500">
        <ShieldAlert className="h-8 w-8 text-slate-600 mb-2" />
        <span>Incident #{incidentId} not found.</span>
        <Link href="/" className="mt-3 text-sky-400 hover:underline">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const colors = severityColor(incident.severity);

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto pb-10">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="p-2 rounded-lg border border-slate-800 bg-night-900 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2 font-mono">
              <span className="text-xl font-bold text-slate-100">Incident #{incident.id}: {incident.title}</span>
              <span className={`text-[10px] uppercase px-2 py-0.5 rounded border font-sans font-bold ${colors.badge}`}>
                {incident.severity}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Opened: {formatTimestamp(incident.created_at)} • Correlated {incident.alerts?.length || 0} alerts
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {incident.status !== "resolved" ? (
            <Button
              size="sm"
              onClick={() => handleStatusChange("resolved")}
              className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs h-8"
            >
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
              Mark Resolved
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleStatusChange("investigating")}
              className="border-slate-700 text-slate-300 text-xs h-8"
            >
              Reopen Case
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={loadIncidentData}
            className="border-slate-700 text-slate-300 text-xs h-8"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* MITRE ATT&CK Badges Bar */}
      {incident.mitre_techniques && incident.mitre_techniques.length > 0 && (
        <div className="p-3 rounded-xl border border-slate-800 bg-night-900/60 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Mapped MITRE Techniques:</span>
          {incident.mitre_techniques.map((tech) => (
            <span
              key={tech}
              className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950/80 border border-sky-800 text-sky-300"
            >
              {tech}
            </span>
          ))}
        </div>
      )}

      {/* Main Tabs */}
      <Tabs defaultValue="report" className="w-full">
        <TabsList className="bg-night-950 border border-slate-800">
          <TabsTrigger value="report" className="gap-1.5 text-xs">
            <FileText className="h-3.5 w-3.5" />
            NIST Incident Report
          </TabsTrigger>
          <TabsTrigger value="reasoning" className="gap-1.5 text-xs">
            <Clock className="h-3.5 w-3.5" />
            Agent Reasoning
          </TabsTrigger>
          <TabsTrigger value="graph" className="gap-1.5 text-xs">
            <Share2 className="h-3.5 w-3.5" />
            Attack Topology
          </TabsTrigger>
          <TabsTrigger value="alerts" className="gap-1.5 text-xs">
            <ShieldAlert className="h-3.5 w-3.5" />
            Correlated Alerts ({incident.alerts?.length || 0})
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: NIST Report */}
        <TabsContent value="report" className="mt-4">
          <Card className="border-slate-800 bg-night-900/80">
            <CardHeader className="p-4 pb-2 border-b border-slate-800/80">
              <CardTitle className="text-sm font-semibold text-slate-100 flex items-center justify-between">
                <span>Autonomous NIST SP 800-61 Incident Report</span>
                <Badge variant="outline" className="font-mono text-[10px] text-sky-400 border-sky-500/30">
                  AI Generated
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 font-sans text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {incident.agent_report || (
                <div className="text-slate-500 font-mono text-xs py-6 text-center">
                  No automated incident report compiled yet. Click &quot;Agent Reasoning&quot; tab to invoke the swarm.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Agent Reasoning */}
        <TabsContent value="reasoning" className="mt-4">
          <AgentReasoning
            incidentId={incident.id}
            initialSteps={reasoningSteps}
            onAgentsCompleted={loadIncidentData}
          />
        </TabsContent>

        {/* Tab 3: Attack Graph */}
        <TabsContent value="graph" className="mt-4">
          <AttackGraph incidentId={incident.id} height={520} />
        </TabsContent>

        {/* Tab 4: Correlated Alerts */}
        <TabsContent value="alerts" className="mt-4">
          <Card className="border-slate-800 bg-night-900/80">
            <CardContent className="p-0 font-mono text-xs divide-y divide-slate-800/80">
              {(!incident.alerts || incident.alerts.length === 0) ? (
                <div className="py-8 text-center text-slate-500 text-xs">
                  No alerts linked directly to this case.
                </div>
              ) : (
                incident.alerts.map((alt) => (
                  <div key={alt.id} className="p-4 flex items-center justify-between hover:bg-slate-800/30">
                    <div>
                      <div className="font-bold text-slate-200 flex items-center gap-2">
                        <span>#{alt.id} {alt.type}</span>
                        <span className={`text-[10px] uppercase px-1.5 py-0.2 rounded border font-sans font-bold ${severityColor(alt.severity).badge}`}>
                          {alt.severity}
                        </span>
                      </div>
                      <div className="text-slate-400 mt-1">
                        {alt.src_ip} → {alt.dst_ip} • Risk: {formatRiskScore(alt.risk_score)}
                      </div>
                    </div>
                    <div className="text-slate-500 text-[11px] font-sans">
                      {formatTimestamp(alt.timestamp)}
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
