<<<<<<< HEAD
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

## Quick start

Prerequisites: Docker Desktop, Python 3.11+, Node.js 20+, optional [Ollama](https://ollama.com) with `llama3.2:3b`.

```bash
# 1. Generate synthetic alerts (no 12 GB CIC download required)
python pipelines/generate_synthetic.py

# 2. Start infrastructure + apps
docker compose up --build

# 3. API: http://localhost:8000/docs
#    UI:  http://localhost:3000
```

Local (without Docker for the app processes):

```bash
docker compose up -d postgres neo4j qdrant redis
cd backend && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000

cd frontend && npm install && npm run dev
```

Index MITRE (after Neo4j/Qdrant are up):

```bash
python pipelines/index_mitre.py
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
=======
# ARTIC-Sec-Real-Time-Agentic-RAG-for-Autonomous-Cyber-Threat-Intelligence-and-Incident-Response-
ARTIC-Sec analyzes security logs in under 5 seconds using ML anomaly detection, streaming RAG, and specialized AI agents for reconnaissance, analysis, response, and reporting. Built-in guardrails prevent prompt injection, RAG poisoning, and tool hijacking. It generates MITRE ATT&amp;CK forensic reports and supports human-approved containment actions.
>>>>>>> 62fb693b6ce5049152b3b33ad3aa586f9a8a66bf
