# ARTIC-Sec

**Agentic Real-Time Intelligent Cybersecurity** — a production-grade SOC platform that combines supervised/unsupervised ML, hybrid RAG (Qdrant + BM25 + Neo4j), and a LangGraph multi-agent workflow for detection, investigation, containment recommendations, and NIST SP 800-61 incident reporting.

## Capabilities

- Isolation Forest anomaly detection and XGBoost threat classification with ONNX Runtime inference
- Hybrid retrieval over MITRE ATT&CK (vectors, keyword, knowledge graph)
- LangGraph agents: recon, analysis, response, report, guardrails
- Prompt-injection detection, action allow-lists, internal-IP protection, rate limits, audit trail
- FastAPI REST + SSE insights + WebSocket alert fan-out
- Next.js 16 SOC dashboard (metrics, alert feed, attack graph, threat map, agent reasoning)

## Architecture

```
Ingest (Kafka | DB poll | CSV) → ML (anomaly + XGBoost/ONNX)
        → PostgreSQL alerts → LangGraph orchestrator
        → RAG (Qdrant + Neo4j) → Guardrails → Report
Frontend ← REST / SSE / WebSocket
```

See [docs/architecture.md](docs/architecture.md).

## Quick start (no Kafka)

Prerequisites: Python 3.11+, Node.js 20+, and Docker Desktop (optional - see `--no-docker`). [Ollama](https://ollama.com) with `llama3.2:3b` is optional; without it agents use rule-based fallbacks.

**One command, any OS:**

```bash
python scripts/run_local.py              # first run: full setup, then starts everything
python scripts/run_local.py --no-docker  # no Docker at all: SQLite, MITRE-RAG store disabled
```

Then open **http://localhost:3000** (dashboard) and **http://localhost:8000/docs** (API). Kafka is never started; alerts are read by polling the database (`KAFKA_ENABLED=false`).

**Or step by step** (Linux/macOS via Make):

```bash
make bootstrap     # infra (no Kafka) + deps + synthetic data + seed + train models + MITRE index
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

Individual steps: `make infra`, `make synthetic`, `make seed`, `make train`, `make mitre-index`. Pipeline scripts can be run from any directory (no `PYTHONPATH` needed).

Full Docker mode: `cp backend/.env.example backend/.env && docker compose up --build` (add `--profile kafka` only if you want Kafka).

## SOAR response playbooks

The response agent decides *what* to do; the playbook layer controls *whether and how* it happens.

```
POST /api/v1/actions/propose/{alert_id}   -> runs response agent + guardrails, stores a PlaybookAction
     low-risk + guardrails pass + AUTO_EXECUTE_LOW_RISK=true  -> auto_executed
     otherwise                                                -> pending_approval
POST /api/v1/actions/{id}/approve         -> approver/admin; re-checks guardrails, executes, audit-logs
POST /api/v1/actions/{id}/reject          -> approver/admin
GET  /api/v1/actions?status=pending_approval
```

Supported actions: `BLOCK_IP, ISOLATE_HOST, DISABLE_ACCOUNT, REVOKE_CREDENTIALS, QUARANTINE_FILE, RATE_LIMIT, MONITOR, ESCALATE`. Connectors in `backend/app/agents/playbook_executor.py` are **simulated** (they record what they would do); replace each `_exec_*` body with a real firewall/EDR/IdP API call to go live. Set `SLACK_WEBHOOK_URL` for notifications. UI: **Response Playbooks** page (`/actions`, shortcut `G P`).

## Auth and RBAC

Off by default. Set `AUTH_ENABLED=true` and a strong `SECRET_KEY` in `backend/.env` to enforce login.

| Role | Can do |
| --- | --- |
| analyst | view, propose actions (default for self-registration) |
| approver | + approve/reject actions, list users |
| admin | + change user roles |

`POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `GET /api/v1/auth/users`, `PATCH /api/v1/auth/users/{id}/role`. Self-registration can never create anything above analyst. The first admin is created by promoting a user directly in the DB:

```sql
UPDATE users SET role='admin' WHERE username='yourname';
```

(SQLite mode: `sqlite3 backend/articsec.db`.) Login UI at `/login`.

## Live threat intelligence

Set `ABUSEIPDB_API_KEY` and/or `VIRUSTOTAL_API_KEY` in `backend/.env`. The recon agent then enriches public source IPs with live reputation data (Redis-cached, `THREAT_INTEL_CACHE_TTL_SECONDS`), boosts `intel_confidence`, and raises `risk_score` by 0.15 on a malicious verdict. With no keys, or when offline, it silently falls back to MITRE-only enrichment.

## ML models

Models are not shipped. `python pipelines/train_models.py` trains an Isolation Forest and an XGBoost classifier (with holdout metrics) into `backend/app/ml/models/`; restart the backend to load them. Without trained files the app trains a small fallback model at startup.

## Tests

```bash
cd backend && python -m pytest tests -q     # 22 tests
cd frontend && npx tsc --noEmit
```

## Documentation

| Doc | Description |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/api.md](docs/api.md) | HTTP / WS / SSE |
| [docs/deployment.md](docs/deployment.md) | Production deployment |

## Citation

If you use ARTIC-Sec in academic work, cite the draft in `docs/paper/`.

## License

Research / internal use. CIC-IDS2017 remains subject to the University of New Brunswick license.
