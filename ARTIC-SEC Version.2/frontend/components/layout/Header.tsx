"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, Search, ShieldCheck, Activity, Terminal, ShieldAlert } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useAlertsStore } from "@/hooks/useAlerts";

export function Header() {
  const router = useRouter();
  const { connected } = useWebSocket();
  const totalAlerts = useAlertsStore((s) => s.total);
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/alerts?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-night-950/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-6">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative h-9 w-9 overflow-hidden rounded-lg border border-sky-500/30 bg-night-900 p-1 shadow-inner group-hover:border-sky-400/60 transition-colors">
            <Image src="/logo.svg" alt="ARTIC-Sec Logo" width={32} height={32} className="object-contain" priority />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold tracking-wider text-slate-100 flex items-center gap-1.5 font-mono">
              ARTIC<span className="text-sky-400">-Sec</span>
              <span className="text-[10px] uppercase font-semibold tracking-widest px-1.5 py-0.5 rounded border border-sky-500/30 bg-sky-500/10 text-sky-400">
                v1.0
              </span>
            </span>
            <span className="text-[10px] text-slate-400 -mt-0.5 tracking-tight font-sans">
              Autonomous Threat Intelligence & Cyber Response
            </span>
          </div>
        </Link>
      </div>

      <div className="flex flex-1 max-w-md mx-8">
        <form onSubmit={handleSearch} className="relative w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search alerts, IPs, MITRE techniques (e.g. T1046, 192.168.1.1)..."
            className="w-full h-9 pl-9 pr-4 rounded-lg bg-night-900/90 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-sky-500/80 focus:ring-1 focus:ring-sky-500/50 transition-all font-mono"
          />
        </form>
      </div>

      <div className="flex items-center gap-4">
        {/* Real-time Connection Indicator */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full border border-slate-800 bg-night-900/60 text-xs">
          <span className="relative flex h-2 w-2">
            {connected ? (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </>
            ) : (
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500 animate-pulse"></span>
            )}
          </span>
          <span className="text-[11px] font-medium text-slate-300">
            {connected ? "SOC Link Live" : "Connecting..."}
          </span>
        </div>

        {/* Notifications Icon with Total Alerts */}
        <Link
          href="/alerts"
          className="relative p-2 rounded-lg border border-slate-800 bg-night-900/60 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Active Alerts"
        >
          <Bell className="h-4 w-4" />
          {totalAlerts > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-4 px-1 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white shadow-md">
              {totalAlerts > 99 ? "99+" : totalAlerts}
            </span>
          )}
        </Link>
      </div>
    </header>
  );
}
