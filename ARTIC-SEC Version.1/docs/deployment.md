# Deployment

## Prerequisites

- Docker 24+ / Compose v2
- Python 3.11 (local pipelines)
- Node.js 20+ (local UI)
- Optional: Ollama with `ollama pull llama3.2:3b`

## Docker Compose (recommended)

```bash
python pipelines/generate_synthetic.py
docker compose up --build
```

- UI: http://localhost:3000
- API: http://localhost:8000/docs
- Neo4j browser: http://localhost:7474 (neo4j / changeme)
- Qdrant: http://localhost:6333

Seed alerts (from host, with venv pointing at compose Postgres):

```bash
cd backend
copy .env.example .env
pip install -r requirements.txt
cd ..
python pipelines/seed_alerts.py --limit 500
python pipelines/index_mitre.py
```

## Environment

Copy `backend/.env.example`. In production:

- Set `SECRET_KEY` to a 64-byte random value
- `AUTH_ENABLED=true` and issue JWTs from your IdP
- Change Neo4j/Postgres passwords
- Restrict `CORS_ORIGINS`
- Keep `KAFKA_ENABLED=true` only if the kafka profile is running

## Kafka profile

```bash
docker compose --profile kafka up
```

Set `KAFKA_ENABLED=true` and `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` on the backend service.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Backend unhealthy | `docker compose logs backend`, Postgres health |
| Empty dashboard | Run `pipelines/seed_alerts.py` |
| Graph empty | Start Neo4j, run `pipelines/index_mitre.py` |
| LLM fallback text | Start Ollama on host; backend uses `host.docker.internal:11434` |
| WebSocket drops | Reverse proxy must allow Upgrade headers |

## Production notes

- Run uvicorn with multiple workers behind an API gateway that terminates TLS.
- Mount model artifacts (`backend/app/ml/models`) as a volume after training on CIC-IDS2017.
- Do not expose Neo4j bolt or Postgres ports publicly.
- Agent execute path is simulated; wire ticketing/SOAR only behind the guardrail allow-list.
