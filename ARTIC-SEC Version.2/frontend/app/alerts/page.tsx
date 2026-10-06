"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ShieldAlert,
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { getAlerts, updateAlertStatus, type AlertItem } from "@/lib/api";
import { formatTimestamp, formatRiskScore, severityColor } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";

function AlertsContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("q") || "";
  const { toast } = useToast();

  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [loading, setLoading] = useState(true);

  const [severity, setSeverity] = useState<string>("all");
  const [status, setStatus] = useState<string>("all");
  const [search, setSearch] = useState(initialSearch);
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);

  const fetchAlertsData = async () => {
    setLoading(true);
    try {
      const res = await getAlerts({
        limit: pageSize,
        offset: (page - 1) * pageSize,
        severity: severity === "all" ? undefined : severity,
        status: status === "all" ? undefined : status,
      });
      setAlerts(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      toast({ title: "Failed to load alerts", description: err.message, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertsData();
  }, [page, severity, status]);

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await updateAlertStatus(id, newStatus);
      toast({ title: `Alert #${id} marked as ${newStatus}`, type: "success" });
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: newStatus } : a))
      );
      if (selectedAlert && selectedAlert.id === id) {
        setSelectedAlert({ ...selectedAlert, status: newStatus });
      }
    } catch (err: any) {
      toast({ title: "Failed to update alert", description: err.message, type: "error" });
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      a.type.toLowerCase().includes(q) ||
      a.src_ip.toLowerCase().includes(q) ||
      a.dst_ip.toLowerCase().includes(q) ||
      (a.mitre_technique && a.mitre_technique.toLowerCase().includes(q))
    );
  });

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-rose-400" />
            Security Alert Management
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Browse, triage, and filter deep-packet telemetry and anomaly detections.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAlertsData}
            className="h-8 gap-1.5 text-xs border-slate-700"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="border-slate-800 bg-night-900/80">
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-1 min-w-[260px] max-w-md items-center relative">
            <Search className="absolute left-3 h-4 w-4 text-slate-400" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by attack type, IP, or MITRE ID..."
              className="pl-9 h-8 text-xs font-mono"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Severity Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <span>Severity:</span>
              <select
                value={severity}
                onChange={(e) => {
                  setSeverity(e.target.value);
                  setPage(1);
                }}
                className="h-8 rounded-md bg-night-950 border border-slate-700 text-xs text-slate-200 px-2 focus:outline-none"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <span>Status:</span>
              <select
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
                className="h-8 rounded-md bg-night-950 border border-slate-700 text-xs text-slate-200 px-2 focus:outline-none"
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="investigating">Investigating</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alert Table */}
      <Card className="border-slate-800 bg-night-900/80 overflow-hidden">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[80px]">ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Source IP</TableHead>
                <TableHead>Destination IP</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Timestamp</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-xs text-slate-500 font-mono">
                    Loading security alert records...
                  </TableCell>
                </TableRow>
              ) : filteredAlerts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-12 text-xs text-slate-500 font-mono">
                    No alerts match the selected criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredAlerts.map((alert) => {
                  const colors = severityColor(alert.severity);
                  const isHigh = alert.risk_score >= 0.7;

                  return (
                    <TableRow
                      key={alert.id}
                      className="cursor-pointer font-mono text-xs hover:bg-slate-800/40"
                      onClick={() => setSelectedAlert(alert)}
                    >
                      <TableCell className="font-bold text-slate-400">#{alert.id}</TableCell>
                      <TableCell className="font-semibold text-slate-200">
                        <div className="flex items-center gap-2">
                          <span>{alert.type}</span>
                          {alert.mitre_technique && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-950 border border-sky-800 text-sky-400">
                              {alert.mitre_technique}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-300">{alert.src_ip}</TableCell>
                      <TableCell className="text-slate-400">{alert.dst_ip}</TableCell>
                      <TableCell>
                        <span className={isHigh ? "font-bold text-rose-400" : "text-slate-300"}>
                          {formatRiskScore(alert.risk_score)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border font-sans font-bold ${colors.badge}`}>
                          {alert.severity}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={`text-[10px] capitalize font-mono ${
                            alert.status === "resolved"
                              ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10"
                              : alert.status === "investigating"
                              ? "border-amber-500/30 text-amber-400 bg-amber-500/10"
                              : "border-slate-700 text-slate-300"
                          }`}
                        >
                          {alert.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-400 font-sans text-[11px]">
                        {formatTimestamp(alert.timestamp)}
                      </TableCell>
                      <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          {alert.status !== "resolved" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleStatusChange(alert.id, "resolved")}
                              className="h-7 px-2 text-[11px] text-emerald-400 hover:bg-emerald-950/40"
                            >
                              Resolve
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setSelectedAlert(alert)}
                            className="h-7 w-7 text-slate-400 hover:text-white"
                          >
                            <Eye className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>

          {/* Pagination Controls */}
          <div className="p-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
            <div>
              Showing {filteredAlerts.length} of {total} total alerts
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="h-7 px-2.5 text-xs border-slate-700"
              >
                <ChevronLeft className="h-3.5 w-3.5 mr-1" />
                Previous
              </Button>
              <span className="px-2 font-semibold text-slate-200">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages || loading}
                onClick={() => setPage((p) => p + 1)}
                className="h-7 px-2.5 text-xs border-slate-700"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alert Details Dialog */}
      {selectedAlert && (
        <Dialog open={!!selectedAlert} onOpenChange={() => setSelectedAlert(null)}>
          <DialogContent className="max-w-2xl bg-night-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
                <span>Alert #{selectedAlert.id}: {selectedAlert.type}</span>
                <span className={`text-[10px] uppercase px-2 py-0.5 rounded border font-sans font-bold ${severityColor(selectedAlert.severity).badge}`}>
                  {selectedAlert.severity}
                </span>
              </DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                Deep telemetry inspection and correlated indicators of compromise.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-2 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-night-950 border border-slate-800">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-bold">Source IP</span>
                  <div className="text-slate-200 mt-0.5">{selectedAlert.src_ip}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-bold">Destination IP</span>
                  <div className="text-slate-200 mt-0.5">{selectedAlert.dst_ip}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-bold">Anomaly Score</span>
                  <div className="text-rose-400 font-bold mt-0.5">{formatRiskScore(selectedAlert.risk_score)}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-bold">MITRE Technique</span>
                  <div className="text-sky-400 mt-0.5">{selectedAlert.mitre_technique || "N/A"}</div>
                </div>
              </div>

              {selectedAlert.payload_preview && (
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-bold">Packet Hex / Payload Preview</span>
                  <pre className="mt-1 p-3 rounded-lg bg-night-950 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap">
                    {selectedAlert.payload_preview}
                  </pre>
                </div>
              )}

              <div className="flex items-center justify-between pt-2">
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(selectedAlert.id, "investigating")}
                    className="h-8 text-xs border-amber-700/60 text-amber-300 hover:bg-amber-950/30"
                  >
                    Investigate
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(selectedAlert.id, "resolved")}
                    className="h-8 text-xs border-emerald-700/60 text-emerald-300 hover:bg-emerald-950/30"
                  >
                    Mark Resolved
                  </Button>
                </div>

                {selectedAlert.incident_id && (
                  <Link
                    href={`/incidents/${selectedAlert.incident_id}`}
                    className="inline-flex items-center gap-1.5 text-xs text-sky-400 hover:underline font-sans"
                  >
                    <span>View Incident Case #{selectedAlert.incident_id}</span>
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

export default function AlertsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-96 items-center justify-center font-mono text-xs text-slate-500">
          Loading Security Alerts Stream...
        </div>
      }
    >
      <AlertsContent />
    </Suspense>
  );
}
