"use client";

import React, { useState, useEffect, useRef } from "react";
import { Bot, Sparkles, Send, Copy, Check, Terminal, ShieldCheck } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface InsightEvent {
  id: string;
  insight: string;
  alerts: number[];
  timestamp: string;
}

export function AIInsights() {
  const [streamInsights, setStreamInsights] = useState<InsightEvent[]>([]);
  const [query, setQuery] = useState("");
  const [queryResponse, setQueryResponse] = useState<string | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const sseUrl =
      (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1/insights";

    try {
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.addEventListener("insight", (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data);
          const newEntry: InsightEvent = {
            id: Math.random().toString(36).substring(2, 9),
            insight: parsed.insight,
            alerts: parsed.alerts || [],
            timestamp: new Date().toLocaleTimeString(),
          };
          setStreamInsights((prev) => [newEntry, ...prev.slice(0, 8)]);
        } catch (err) {
          console.warn("SSE parse error", err);
        }
      });

      es.onerror = () => {
        // SSE disconnected, browser will auto-reconnect
      };

      return () => {
        es.close();
      };
    } catch (err) {
      console.warn("SSE connection error", err);
    }
  }, []);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isQuerying) return;

    setIsQuerying(true);
    setQueryResponse("");
    try {
      const res = await fetch(
        (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1/insights/query",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: query }),
        }
      );

      if (!res.body) {
        setQueryResponse("No streaming response body available.");
        setIsQuerying(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let fullText = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        setQueryResponse(fullText);
      }
    } catch (err: any) {
      setQueryResponse(`Analyst AI query error: ${err.message}`);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <Card className="flex flex-col border-slate-800 bg-night-900/80">
      <CardHeader className="p-4 pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-purple-500/10 border border-purple-500/20">
            <Sparkles className="h-4 w-4 text-purple-400" />
          </div>
          <div>
            <CardTitle className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Autonomous AI Analyst Stream
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded border border-purple-500/30 bg-purple-500/10 text-purple-300">
                SSE Live
              </span>
            </CardTitle>
            <p className="text-[11px] text-slate-400">Continuous RAG telemetry synthesis & threat correlation</p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 flex flex-col space-y-4">
        {/* Stream Cards */}
        <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
          {streamInsights.length === 0 ? (
            <div className="p-3 rounded-lg border border-slate-800 bg-night-950/60 text-slate-500 text-xs font-mono flex items-center gap-2">
              <Bot className="h-4 w-4 text-slate-600 animate-pulse" />
              Synthesizing telemetry window... first insight streaming shortly.
            </div>
          ) : (
            streamInsights.map((item) => (
              <div
                key={item.id}
                className="p-3 rounded-lg border border-slate-800/80 bg-night-950/70 hover:border-slate-700 transition-colors text-xs"
              >
                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono mb-1.5">
                  <span className="flex items-center gap-1.5 text-purple-400 font-medium">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Correlation Event ({item.alerts.length} alerts)
                  </span>
                  <div className="flex items-center gap-2">
                    <span>{item.timestamp}</span>
                    <button
                      onClick={() => handleCopy(item.id, item.insight)}
                      className="text-slate-500 hover:text-slate-300 p-0.5"
                      title="Copy insight"
                    >
                      {copiedId === item.id ? (
                        <Check className="h-3 w-3 text-emerald-400" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </button>
                  </div>
                </div>
                <p className="text-slate-200 leading-relaxed font-sans">{item.insight}</p>
              </div>
            ))
          )}
        </div>

        {/* Interactive Query Response if present */}
        {queryResponse && (
          <div className="p-3 rounded-lg border border-sky-500/30 bg-sky-950/20 text-xs font-mono animate-in fade-in-0">
            <div className="flex items-center justify-between text-sky-400 font-semibold mb-1">
              <span>SOC Agent Response</span>
              <button onClick={() => setQueryResponse(null)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>
            <div className="text-slate-200 whitespace-pre-wrap leading-relaxed">{queryResponse}</div>
          </div>
        )}

        {/* SOC AI Analyst Query Input */}
        <form onSubmit={handleQuerySubmit} className="relative flex items-center">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isQuerying}
            placeholder="Ask AI Analyst (e.g., 'What MITRE TTPs match this PortScan + SQLi?')..."
            className="w-full h-9 pl-3 pr-10 rounded-lg bg-night-950 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-purple-500/80 focus:ring-1 focus:ring-purple-500/50 transition-all font-mono"
          />
          <Button
            type="submit"
            size="icon"
            disabled={isQuerying || !query.trim()}
            className="absolute right-1 h-7 w-7 bg-purple-600 hover:bg-purple-500 text-white rounded-md"
          >
            <Send className="h-3.5 w-3.5" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
