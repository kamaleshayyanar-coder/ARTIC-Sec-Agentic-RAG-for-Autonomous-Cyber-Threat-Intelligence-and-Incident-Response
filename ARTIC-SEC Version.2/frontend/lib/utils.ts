import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatTimestamp(date: string | Date | number | null | undefined): string {
  if (!date) return "—";
  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) return String(date);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).format(d);
  } catch {
    return String(date);
  }
}

export function formatRiskScore(score: number | null | undefined): string {
  if (score === null || score === undefined || isNaN(score)) return "0%";
  const pct = Math.round(score * 100);
  return `${pct}%`;
}

export function severityColor(severity: string | null | undefined): {
  bg: string;
  text: string;
  border: string;
  badge: string;
} {
  const norm = (severity || "").toLowerCase().trim();
  switch (norm) {
    case "critical":
      return {
        bg: "bg-red-950/40",
        text: "text-rose-400",
        border: "border-rose-800/60",
        badge: "bg-rose-500/10 text-rose-400 border-rose-500/30",
      };
    case "high":
      return {
        bg: "bg-orange-950/40",
        text: "text-amber-400",
        border: "border-amber-800/60",
        badge: "bg-amber-500/10 text-amber-400 border-amber-500/30",
      };
    case "medium":
      return {
        bg: "bg-yellow-950/30",
        text: "text-yellow-400",
        border: "border-yellow-700/50",
        badge: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
      };
    case "low":
    default:
      return {
        bg: "bg-slate-900/50",
        text: "text-slate-400",
        border: "border-slate-800",
        badge: "bg-slate-800/60 text-slate-300 border-slate-700",
      };
  }
}

export function truncate(text: string | null | undefined, length = 32): string {
  if (!text) return "";
  if (text.length <= length) return text;
  return `${text.slice(0, length)}...`;
}
