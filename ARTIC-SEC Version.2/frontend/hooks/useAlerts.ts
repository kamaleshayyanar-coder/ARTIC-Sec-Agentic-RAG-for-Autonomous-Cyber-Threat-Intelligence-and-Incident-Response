"use client";

import { create } from "zustand";
import { useEffect, useCallback } from "react";
import { type AlertItem, getAlerts, updateAlertStatus as apiUpdateStatus } from "@/lib/api";
import { defaultWebSocketClient } from "@/lib/websocket";

interface AlertsState {
  alerts: AlertItem[];
  total: number;
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: number;
  severityFilter: string | null;
  statusFilter: string | null;
  typeFilter: string | null;
  isPaused: boolean;

  setSeverityFilter: (severity: string | null) => void;
  setStatusFilter: (status: string | null) => void;
  setTypeFilter: (type: string | null) => void;
  setIsPaused: (paused: boolean) => void;
  togglePause: () => void;
  addAlert: (alert: AlertItem) => void;
  updateAlertStatus: (id: number, status: string) => Promise<void>;
  fetchAlerts: (page?: number) => Promise<void>;
}

export const useAlertsStore = create<AlertsState>((set, get) => ({
  alerts: [],
  total: 0,
  loading: false,
  error: null,
  page: 1,
  pageSize: 50,
  severityFilter: null,
  statusFilter: null,
  typeFilter: null,
  isPaused: false,

  setSeverityFilter: (severity) => {
    set({ severityFilter: severity, page: 1 });
    get().fetchAlerts(1);
  },

  setStatusFilter: (status) => {
    set({ statusFilter: status, page: 1 });
    get().fetchAlerts(1);
  },

  setTypeFilter: (type) => {
    set({ typeFilter: type, page: 1 });
    get().fetchAlerts(1);
  },

  setIsPaused: (paused) => set({ isPaused: paused }),
  togglePause: () => set((state) => ({ isPaused: !state.isPaused })),

  addAlert: (newAlert) => {
    if (get().isPaused) return;
    set((state) => {
      const exists = state.alerts.some((a) => a.id === newAlert.id);
      if (exists) {
        return {
          alerts: state.alerts.map((a) => (a.id === newAlert.id ? { ...a, ...newAlert } : a)),
        };
      }
      return {
        alerts: [newAlert, ...state.alerts].slice(0, 200),
        total: state.total + 1,
      };
    });
  },

  updateAlertStatus: async (id: number, status: string) => {
    try {
      const updated = await apiUpdateStatus(id, status);
      set((state) => ({
        alerts: state.alerts.map((a) => (a.id === id ? { ...a, status: updated.status } : a)),
      }));
    } catch (err: any) {
      console.error("Failed to update status", err);
    }
  },

  fetchAlerts: async (page = 1) => {
    const { pageSize, severityFilter, statusFilter, typeFilter } = get();
    set({ loading: true, error: null });
    try {
      const offset = (page - 1) * pageSize;
      const res = await getAlerts({
        limit: pageSize,
        offset,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        type: typeFilter || undefined,
      });
      set({
        alerts: res.items || [],
        total: res.total || 0,
        page,
        loading: false,
      });
    } catch (err: any) {
      set({ error: err.message || "Failed to load alerts", loading: false });
    }
  },
}));

export function useAlerts() {
  const store = useAlertsStore();

  useEffect(() => {
    store.fetchAlerts();

    const unsub = defaultWebSocketClient.onMessage((msg) => {
      if (msg && msg.event === "alert" && msg.data) {
        store.addAlert(msg.data);
      } else if (msg && msg.id && msg.risk_score !== undefined) {
        store.addAlert(msg);
      }
    });

    return () => {
      unsub();
    };
  }, []);

  return store;
}
