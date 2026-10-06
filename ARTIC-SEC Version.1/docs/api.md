# ARTIC-Sec HTTP API

Base URL: `http://localhost:8000`

Interactive spec: `/docs` (OpenAPI 3).

Authentication: disabled by default (`AUTH_ENABLED=false`). When enabled, send `Authorization: Bearer <JWT>`.

## Alerts

`GET /api/v1/alerts?limit=50&offset=0&severity=high&status=open&type=PortScan`

`GET /api/v1/alerts/{id}`

`GET /api/v1/alerts/geo`

`POST /api/v1/alerts`

```json
{
  "type": "PortScan",
  "src_ip": "203.0.113.10",
  "dst_ip": "10.0.0.5",
  "risk_score": 0.81,
  "severity": "high"
}
```

`PATCH /api/v1/alerts/{id}` — `{ "status": "investigating" }`

`DELETE /api/v1/alerts/{id}` — admin when auth is on

`POST /api/v1/alerts/{id}/investigate` — run LangGraph workflow

## Metrics

`GET /api/v1/metrics`

`GET /api/v1/metrics/hourly`

`GET /api/v1/metrics/severity-distribution`

`GET /api/v1/metrics/attack-types`

## Graph

`GET /api/v1/graph` → `{ "nodes": [...], "links": [...] }`

`GET /api/v1/graph/incident/{incident_id}`

`GET /api/v1/graph/mitre-technique/{technique_id}`

## Insights (SSE)

`GET /api/v1/insights` — `text/event-stream`, event name `insight`

`POST /api/v1/insights/query` — body `{ "question": "...", "alert_id": 1 }`, events `citations`, `token`, `done`

## Incidents

`GET /api/v1/incidents`

`GET /api/v1/incidents/{id}`

`GET /api/v1/incidents/{id}/reasoning`

`POST /api/v1/incidents/{id}/run-agents`

## Agents

`GET /api/v1/agents/status`

`GET /api/v1/agents/audit`

## WebSocket

`WS /ws`

Server sends JSON `{ "event": "alert", "data": { ... } }`. Client may send `ping`.

## Health

`GET /health`
