"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ShieldAlert,
  FolderGit2,
  Share2,
  Bot,
  Activity,
  Cpu,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard, shortcut: "G D" },
  { label: "Alerts Stream", href: "/alerts", icon: ShieldAlert, shortcut: "G A" },
  { label: "Attack Graph", href: "/graph", icon: Share2, shortcut: "G G" },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  // Keyboard navigation shortcuts
  useEffect(() => {
    let lastKey = "";
    let timeout: any;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger when typing in inputs
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      const key = e.key.toLowerCase();
      if (lastKey === "g") {
        if (key === "d") router.push("/");
        else if (key === "a") router.push("/alerts");
        else if (key === "g") router.push("/graph");
        lastKey = "";
        clearTimeout(timeout);
        return;
      }

      if (key === "g") {
        lastKey = "g";
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          lastKey = "";
        }, 1000);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      clearTimeout(timeout);
    };
  }, [router]);

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-night-950/60 flex flex-col justify-between p-4 shrink-0 select-none">
      <div className="space-y-6">
        <div className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          SOC Operations
        </div>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group",
                  isActive
                    ? "bg-sky-500/15 text-sky-400 border border-sky-500/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn("h-4 w-4 transition-colors", isActive ? "text-sky-400" : "text-slate-400 group-hover:text-slate-200")} />
                  <span>{item.label}</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono border border-slate-800 rounded px-1.5 py-0.5 opacity-60 group-hover:opacity-100">
                  {item.shortcut}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-slate-800/80 pt-4 space-y-3">
        <div className="p-3 rounded-lg border border-slate-800/90 bg-night-900/80">
          <div className="flex items-center justify-between text-xs text-slate-300 font-semibold">
            <span className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-sky-400" />
              Agent Core
            </span>
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
          <p className="mt-1.5 text-[11px] text-slate-400 leading-relaxed">
            LangGraph multi-agent orchestrator: Recon, Analysis, Response & Guardrails online.
          </p>
        </div>
      </div>
    </aside>
  );
}
