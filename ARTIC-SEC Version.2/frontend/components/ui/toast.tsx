"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { X, AlertTriangle, CheckCircle, Info } from "lucide-react";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  type?: "success" | "error" | "warning" | "info";
}

interface ToastContextType {
  toast: (props: Omit<ToastItem, "id">) => void;
  removeToast: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastItem[]>([]);

  const toast = React.useCallback(({ title, description, type = "info" }: Omit<ToastItem, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast, removeToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => {
          const isError = t.type === "error";
          const isSuccess = t.type === "success";
          const isWarning = t.type === "warning";
          return (
            <div
              key={t.id}
              className={cn(
                "pointer-events-auto flex items-start gap-3 p-4 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 animate-in slide-in-from-bottom-5",
                isError && "bg-rose-950/90 border-rose-800 text-rose-100",
                isSuccess && "bg-emerald-950/90 border-emerald-800 text-emerald-100",
                isWarning && "bg-amber-950/90 border-amber-800 text-amber-100",
                !isError && !isSuccess && !isWarning && "bg-night-900/95 border-slate-700 text-slate-100"
              )}
            >
              <div className="mt-0.5 shrink-0">
                {isError && <AlertTriangle className="h-5 w-5 text-rose-400" />}
                {isSuccess && <CheckCircle className="h-5 w-5 text-emerald-400" />}
                {isWarning && <AlertTriangle className="h-5 w-5 text-amber-400" />}
                {!isError && !isSuccess && !isWarning && <Info className="h-5 w-5 text-sky-400" />}
              </div>
              <div className="flex-1 text-sm">
                <div className="font-semibold leading-tight">{t.title}</div>
                {t.description && <div className="mt-1 text-xs opacity-80 leading-relaxed">{t.description}</div>}
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="shrink-0 p-1 opacity-60 hover:opacity-100 rounded transition-opacity"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    return {
      toast: (p: any) => console.log("[Toast fallback]", p),
      removeToast: () => {},
    };
  }
  return context;
}
