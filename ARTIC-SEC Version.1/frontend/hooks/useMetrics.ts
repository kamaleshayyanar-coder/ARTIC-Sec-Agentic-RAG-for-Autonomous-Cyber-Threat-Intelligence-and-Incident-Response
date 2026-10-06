"use client";

import { useState, useEffect, useCallback } from "react";
import { getMetrics, getHourlyMetrics, type MetricsData, type HourlyPoint } from "@/lib/api";

const DEFAULT_METRICS: MetricsData = {
  total_alerts: 0,
  high_risk_count: 0,
  mttd_seconds: 0,
  mttr_seconds: 0,
  auto_resolution_rate: 0,
  open_incidents: 0,
  websocket_clients: 0,
};

export function useMetrics(pollIntervalMs = 5000) {
  const [metrics, setMetrics] = useState<MetricsData>(DEFAULT_METRICS);
  const [hourly, setHourly] = useState<HourlyPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAllMetrics = useCallback(async () => {
    try {
      const [m, h] = await Promise.all([getMetrics(), getHourlyMetrics()]);
      setMetrics(m);
      setHourly(h);
      setError(null);
    } catch (err: any) {
      console.warn("Metrics fetch failed:", err.message);
      setError(err.message || "Failed to fetch metrics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllMetrics();
    const interval = setInterval(fetchAllMetrics, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchAllMetrics, pollIntervalMs]);

  return { metrics, hourly, loading, error, refresh: fetchAllMetrics };
}
