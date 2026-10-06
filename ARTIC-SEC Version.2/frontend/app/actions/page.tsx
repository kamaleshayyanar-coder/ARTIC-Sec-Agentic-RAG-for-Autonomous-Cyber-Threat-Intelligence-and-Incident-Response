"use client";

import React, { useCallback, useEffect, useState } from "react";
import { ShieldCheck, RefreshCw, Check, X, LogOut } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import {
  approveAction,
  clearSession,
  getActions,
  getSessionUser,
  rejectAction,
  type PlaybookAction,
} from "@/lib/api";

const FILTERS = ["all", "pending_approval", "executed", "auto_executed", "rejected", "failed"];

export default function ActionsPage() {
  const [items, setItems] = useState<PlaybookAction[]>([]);
  const [filter, setFilter] = useState("pending_approval");
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);

  const load = useCallback(async () => {
    try {
      setItems(await getActions(filter === "all" ? undefined : filter));
      setError(null);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to load actions");
    }
  }, [filter]);

  useEffect(() => {
    setUser(getSessionUser());
  }, []);
  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  async function decide(id: number, approve: boolean) {
    try {
      approve ? await approveAction(id) : await rejectAction(id);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Action failed (approver/admin role required when auth is on)");
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="flex items-center gap-2 text-xl font-semibold">
          <ShieldCheck className="h-5 w-5 text-sky-400" /> Response Playbooks
        </h1>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          {user ? (
            <>
              {user.username} ({user.role})
              <Button size="sm" variant="ghost" onClick={() => { clearSession(); setUser(null); }}>
                <LogOut className="h-3 w-3" />
              </Button>
            </>
          ) : (
            <a href="/login" className="text-sky-400 hover:underline">Sign in</a>
          )}
          <Button size="sm" variant="outline" onClick={load}>
            <RefreshCw className="h-3 w-3" />
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1 text-xs ${
              filter === f ? "border-sky-500 bg-sky-500/20 text-sky-200" : "border-slate-700 text-slate-400"
            }`}
          >
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{String(error)}</p>}

      <Card>
        <CardHeader>
          <CardTitle>Actions ({items.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Why</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>#{a.id}</TableCell>
                  <TableCell className="font-mono text-xs">{a.action_type}</TableCell>
                  <TableCell className="font-mono text-xs">{a.target}</TableCell>
                  <TableCell>{a.severity}</TableCell>
                  <TableCell>{a.risk_score.toFixed(2)}</TableCell>
                  <TableCell>
                    <Badge>{a.status.replace("_", " ")}</Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-xs text-slate-400">{a.justification}</TableCell>
                  <TableCell>
                    {a.status === "pending_approval" && (
                      <div className="flex gap-1">
                        <Button size="sm" onClick={() => decide(a.id, true)}>
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => decide(a.id, false)}>
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {items.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-slate-500">
                    Nothing here. Propose an action from an alert to populate this queue.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
