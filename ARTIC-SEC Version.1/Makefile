.PHONY: install backend-install frontend-install dev up down test lint build clean synthetic mitre-index

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

mitre-index:
	$(PYTHON) pipelines/index_mitre.py

ingest:
	$(PYTHON) pipelines/ingest_cic.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next backend/.pytest_cache
	rm -f backend/app/ml/models/*.pkl backend/app/ml/models/*.onnx
