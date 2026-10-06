# ARTIC-Sec architecture

## Overview

ARTIC-Sec is a SOC copilot: high-volume network events are classified, enriched with MITRE ATT&CK via hybrid RAG, investigated by a LangGraph agent graph, and presented on a real-time analyst console.

```
Kafka|DB poll ─► FastAPI ingest ─► PostgreSQL (alerts, incidents, users)
                         │
                         ├─ Isolation Forest + XGBoost / ONNX
                         ├─ Qdrant (dense) + BM25 + Neo4j (graph)
                         ├─ LangGraph: classify → investigate → analyze → decide → execute → report
                         └─ Guardrails: allow-list, injection scan, internal-IP policy, rate limit, audit
Frontend (Next.js) ◄─ REST / SSE / WebSocket
```

## Component rationale

| Layer | Choice | Why |
| --- | --- | --- |
| API | FastAPI | Async SSE/WebSocket, OpenAPI, Pydantic v2 |
| Relational | PostgreSQL | Alert/incident system of record |
| Graph | Neo4j | MITRE technique/tactic/asset relationships |
| Vectors | Qdrant | Filtered ANN search, payload metadata |
| Cache | Redis | KPI cache + pub/sub |
| Agents | LangGraph | Explicit state machine, streaming traces |
| LLM | Ollama Llama 3.2 3B | Air-gapped SOC constraint |
| ML | XGBoost + Isolation Forest + ONNX | Tabular IDS + zero-day + p95 latency |
| UI | Next.js 16 App Router | Streaming insights, typed client |

## Data flow

1. Event arrives (Kafka topic `security-alerts` or DB poll / CSV seed).
2. Classifier and anomaly detector attach `ml_prediction`, `risk_score`.
3. Alert is persisted; WebSocket clients receive `{event: alert}`.
4. Analyst or automatic hook runs `invoke(alert)`:
   - Recon: hybrid search + graph expansion + source IP history
   - Analysis: JSON hypothesis from LLM (payloads sanitized)
   - Response: policy engine (MONITOR / BLOCK_IP / ISOLATE_HOST / ESCALATE)
   - Guardrail: reject unknown tools, prompt injection, unapproved internal blocks
   - Report: NIST SP 800-61 markdown + IOC JSON
5. Dashboard consumes `/api/v1/metrics`, `/alerts`, `/graph`, `/insights` (SSE).

## Safety

Agent “execute” is **advisory**. No firewall/EDR connector is armed by default. All attempted actions are audit-logged. Human approval is required for high/critical severity and host isolation.
