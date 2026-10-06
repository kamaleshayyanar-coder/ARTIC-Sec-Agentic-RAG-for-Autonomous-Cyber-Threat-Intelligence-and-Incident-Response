.PHONY: install backend-install frontend-install dev up down test lint build clean synthetic mitre-index seed train bootstrap infra kafka-up produce

PYTHON ?= python
PIP ?= pip
NPM ?= npm

install: backend-install frontend-install

backend-install:
	cd backend && $(PYTHON) -m venv .venv || true
	cd backend && .venv/Scripts/pip install -r requirements.txt || .venv/bin/pip install -r requirements.txt

frontend-install:
	cd frontend && $(NPM) install

dev:
	docker compose up --build

up:
	docker compose up -d --build

down:
	docker compose down

test:
	cd backend && .venv/Scripts/python -m pytest tests -q || .venv/bin/python -m pytest tests -q

lint:
	cd backend && .venv/Scripts/python -m ruff check app tests || .venv/bin/python -m ruff check app tests || true
	cd frontend && $(NPM) run lint

build:
	docker compose build

synthetic:
	$(PYTHON) pipelines/generate_synthetic.py

seed:
	$(PYTHON) pipelines/seed_alerts.py --limit 500

train:
	$(PYTHON) pipelines/train_models.py

mitre-index:
	$(PYTHON) pipelines/index_mitre.py

ingest:
	$(PYTHON) pipelines/ingest_cic.py

# Infra containers only -- deliberately does NOT start Kafka (it's behind
# the "kafka" compose profile). Add `--profile kafka` yourself if you want it.
infra:
	docker compose up -d postgres neo4j qdrant redis

# Optional Kafka path: start the broker, then set KAFKA_ENABLED=true in backend/.env
# (KAFKA_BOOTSTRAP_SERVERS=localhost:9094 when the backend runs on your host).
kafka-up:
	docker compose --profile kafka up -d kafka

produce:
	$(PYTHON) pipelines/produce_alerts.py

# One command, no Kafka, no Docker for the app processes themselves:
# starts infra, installs deps, generates+seeds+trains+indexes, then tells
# you the two commands to run the backend/frontend in separate terminals.
bootstrap: infra install
	[ -f backend/.env ] || cp backend/.env.example backend/.env
	$(PYTHON) pipelines/generate_synthetic.py
	$(PYTHON) pipelines/seed_alerts.py --limit 500
	$(PYTHON) pipelines/train_models.py
	$(PYTHON) pipelines/index_mitre.py
	@echo ""
	@echo "Bootstrap complete. Now run, in two separate terminals:"
	@echo "  cd backend && (.venv/bin/activate || .venv\\Scripts\\activate) && uvicorn app.main:app --reload --port 8000"
	@echo "  cd frontend && npm run dev"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next backend/.pytest_cache
	rm -f backend/app/ml/models/*.pkl backend/app/ml/models/*.onnx
