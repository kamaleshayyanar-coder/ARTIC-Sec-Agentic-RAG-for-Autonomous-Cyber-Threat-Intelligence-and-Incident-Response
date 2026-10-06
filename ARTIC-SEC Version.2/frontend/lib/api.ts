import axios, { type AxiosInstance } from "axios";

export interface AlertItem {
  id: number;
  type: string;
  src_ip: string;
  dst_ip: string;
  risk_score: number;
  ml_prediction?: string | null;
  mitre_technique?: string | null;
  severity: "low" | "medium" | "high" | "critical" | string;
  status: "open" | "investigating" | "resolved" | string;
  timestamp: string;
  incident_id?: number | null;
  payload_preview?: string | null;
  latitude?: number;
  longitude?: number;
  lat?: number;
  lon?: number;
}

export interface MetricsData {
  total_alerts: number;
  high_risk_count: number;
  mttd_seconds: number;
  mttr_seconds: number;
  auto_resolution_rate: number;
  open_incidents: number;
  websocket_clients: number;
}

export interface HourlyPoint {
  hour: string;
  count: number;
  high_risk: number;
}

export interface GraphNode {
  id: string;
  name: string;
  type: "attacker" | "technique" | "tactic" | "asset" | string;
  val?: number;
  description?: string;
}

export interface GraphLink {
  source: string | { id: string };
  target: string | { id: string };
  relation?: string;
}

export interface GraphPayload {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface IncidentItem {
  id: number;
  title: string;
  status: string;
  severity: string;
  mitre_techniques: string[];
  agent_report?: string | null;
  created_at: string;
  resolved_at?: string | null;
  alerts: AlertItem[];
}

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  status: "active" | "idle" | "busy" | "error";
  last_run: string;
  current_task: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? "http://localhost:8000" : process.env.BACKEND_INTERNAL_URL || "http://localhost:8000");

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("artic_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail || err.message;
    console.error(`[API Error] ${err.config?.url}:`, detail);
    return Promise.reject(err);
  }
);

export async function getAlerts(params: {
  limit?: number;
  offset?: number;
  severity?: string;
  status?: string;
  type?: string;
}): Promise<{ items: AlertItem[]; total: number; page: number; page_size: number }> {
  const res = await apiClient.get("/api/v1/alerts", { params });
  return res.data;
}

export async function getAlert(id: number): Promise<AlertItem> {
  const res = await apiClient.get(`/api/v1/alerts/${id}`);
  return res.data;
}

export async function updateAlertStatus(id: number, status: string): Promise<AlertItem> {
  const res = await apiClient.patch(`/api/v1/alerts/${id}`, { status });
  return res.data;
}

export async function getGeoAlerts(limit = 100): Promise<AlertItem[]> {
  const res = await apiClient.get("/api/v1/alerts/geo", { params: { limit } });
  return res.data;
}

export async function getMetrics(): Promise<MetricsData> {
  const res = await apiClient.get("/api/v1/metrics");
  return res.data;
}

export async function getHourlyMetrics(): Promise<HourlyPoint[]> {
  const res = await apiClient.get("/api/v1/metrics/hourly");
  return res.data;
}

export async function getGraph(incidentId?: number): Promise<GraphPayload> {
  const url = incidentId ? `/api/v1/graph/incident/${incidentId}` : "/api/v1/graph";
  const res = await apiClient.get(url);
  return res.data;
}

export async function getTechnique(id: string): Promise<any> {
  const res = await apiClient.get(`/api/v1/graph/mitre-technique/${id}`);
  return res.data;
}

export async function getIncidents(params?: {
  limit?: number;
  offset?: number;
  status?: string;
}): Promise<{ items: IncidentItem[]; total: number }> {
  const res = await apiClient.get("/api/v1/incidents", { params });
  return res.data;
}

export async function getIncident(id: number): Promise<IncidentItem> {
  const res = await apiClient.get(`/api/v1/incidents/${id}`);
  return res.data;
}

export async function updateIncident(id: number, data: Partial<IncidentItem>): Promise<IncidentItem> {
  const res = await apiClient.patch(`/api/v1/incidents/${id}`, data);
  return res.data;
}

export async function getIncidentReasoning(id: number): Promise<{ steps: any[]; message?: string }> {
  const res = await apiClient.get(`/api/v1/incidents/${id}/reasoning`);
  return res.data;
}

export async function runIncidentAgents(id: number): Promise<{ incident_id: number; steps: any[]; report: any }> {
  const res = await apiClient.post(`/api/v1/incidents/${id}/run-agents`);
  return res.data;
}

export async function getAgentStatus(): Promise<{ agents: AgentInfo[]; websocket_clients: number; ts: string }> {
  const res = await apiClient.get("/api/v1/agents/status");
  return res.data;
}

// ---------- Auth / RBAC ----------
export interface AuthToken {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
}

export async function login(username: string, password: string): Promise<AuthToken> {
  const res = await apiClient.post("/api/v1/auth/login", { username, password });
  return res.data;
}

export async function register(username: string, email: string, password: string): Promise<AuthToken> {
  const res = await apiClient.post("/api/v1/auth/register", { username, email, password });
  return res.data;
}

export function saveSession(t: AuthToken) {
  localStorage.setItem("artic_token", t.access_token);
  localStorage.setItem("artic_user", JSON.stringify({ username: t.username, role: t.role }));
}

export function clearSession() {
  localStorage.removeItem("artic_token");
  localStorage.removeItem("artic_user");
}

export function getSessionUser(): { username: string; role: string } | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem("artic_user") || "null");
  } catch {
    return null;
  }
}

// ---------- SOAR playbook actions ----------
export interface PlaybookAction {
  id: number;
  alert_id?: number | null;
  action_type: string;
  target: string;
  severity: string;
  risk_score: number;
  status: "pending_approval" | "approved" | "rejected" | "executed" | "auto_executed" | "failed" | string;
  justification?: string | null;
  created_by: string;
  decided_by?: string | null;
  created_at?: string | null;
  decided_at?: string | null;
  executed_at?: string | null;
}

export async function getActions(status?: string): Promise<PlaybookAction[]> {
  const res = await apiClient.get("/api/v1/actions", { params: status ? { status } : {} });
  return res.data;
}

export async function proposeAction(alertId: number): Promise<PlaybookAction> {
  const res = await apiClient.post(`/api/v1/actions/propose/${alertId}`);
  return res.data;
}

export async function approveAction(id: number, note?: string): Promise<PlaybookAction> {
  const res = await apiClient.post(`/api/v1/actions/${id}/approve`, { note });
  return res.data;
}

export async function rejectAction(id: number, note?: string): Promise<PlaybookAction> {
  const res = await apiClient.post(`/api/v1/actions/${id}/reject`, { note });
  return res.data;
}
