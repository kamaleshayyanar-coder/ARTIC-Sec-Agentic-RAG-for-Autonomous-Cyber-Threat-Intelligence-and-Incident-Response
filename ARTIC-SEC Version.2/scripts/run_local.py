#!/usr/bin/env python3
"""One-command local runner for ARTIC-Sec (no Kafka). Works on Windows/macOS/Linux.

    python scripts/run_local.py            # setup (first run) + start backend & frontend
    python scripts/run_local.py --setup    # only do setup
    python scripts/run_local.py --no-docker  # skip Docker; backend falls back to SQLite

What it does, in order:
  1. (unless --no-docker) docker compose up -d postgres neo4j qdrant redis   [Kafka is NOT started]
  2. creates backend/.venv and pip installs requirements  (first run only)
  3. copies backend/.env.example -> backend/.env          (first run only)
  4. generates synthetic alerts, seeds the DB, trains the ML models, indexes MITRE (first run only)
  5. npm install in frontend                               (first run only)
  6. starts uvicorn (:8000) and next dev (:3000) and stops both on Ctrl+C
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
IS_WIN = os.name == "nt"
VENV_PY = BACKEND / ".venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")
MARKER = ROOT / "data" / ".bootstrapped"


def run(cmd, cwd=ROOT, check=True, **kw):
    print(f"\n$ {' '.join(map(str, cmd))}")
    return subprocess.run(list(map(str, cmd)), cwd=cwd, check=check, shell=IS_WIN and cmd[0] == "npm", **kw)


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def wait_for_postgres(timeout=60) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        r = subprocess.run(
            ["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "articsec"],
            cwd=ROOT, capture_output=True,
        )
        if r.returncode == 0:
            return True
        time.sleep(2)
    return False


def setup(use_docker: bool) -> None:
    if use_docker:
        if not have("docker"):
            sys.exit("Docker not found. Install Docker Desktop, or re-run with --no-docker (SQLite fallback).")
        run(["docker", "compose", "up", "-d", "postgres", "neo4j", "qdrant", "redis"])
        print("waiting for Postgres ...")
        if not wait_for_postgres():
            print("! Postgres not ready after 60s; continuing (backend will fall back to SQLite)")

    if not VENV_PY.exists():
        run([sys.executable, "-m", "venv", BACKEND / ".venv"])
        run([VENV_PY, "-m", "pip", "install", "-q", "--upgrade", "pip"])
        run([VENV_PY, "-m", "pip", "install", "-q", "-r", BACKEND / "requirements.txt"])

    env_file = BACKEND / ".env"
    if not env_file.exists():
        shutil.copy(BACKEND / ".env.example", env_file)
        print("created backend/.env from .env.example")
    if not use_docker:
        txt = env_file.read_text()
        if "sqlite" not in txt:
            lines = [("DATABASE_URL=sqlite:///./articsec.db" if l.startswith("DATABASE_URL=") else l) for l in txt.splitlines()]
            env_file.write_text("\n".join(lines) + "\n")
            print("no-docker mode: DATABASE_URL -> sqlite")

    if not MARKER.exists():
        run([VENV_PY, "pipelines/generate_synthetic.py", "--n", "10000"])
        run([VENV_PY, "pipelines/seed_alerts.py", "--limit", "500"])
        run([VENV_PY, "pipelines/train_models.py", "--skip-onnx"])
        if use_docker:
            run([VENV_PY, "pipelines/index_mitre.py"], check=False)  # needs Qdrant/Neo4j; non-fatal
        MARKER.parent.mkdir(exist_ok=True)
        MARKER.write_text("ok")

    if not (FRONTEND / "node_modules").exists():
        if not have("npm"):
            sys.exit("Node.js/npm not found. Install Node 20+.")
        run(["npm", "install", "--no-audit", "--no-fund"], cwd=FRONTEND)


def serve() -> None:
    env = {**os.environ, "PYTHONPATH": str(BACKEND)}
    procs = [
        subprocess.Popen([str(VENV_PY), "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"], cwd=BACKEND, env=env),
        subprocess.Popen(["npm", "run", "dev"], cwd=FRONTEND, shell=IS_WIN),
    ]
    print("\n  Dashboard : http://localhost:3000\n  API docs  : http://localhost:8000/docs\n  Ctrl+C to stop\n")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--setup", action="store_true", help="only run setup")
    ap.add_argument("--no-docker", action="store_true", help="skip Docker; use SQLite")
    a = ap.parse_args()
    setup(use_docker=not a.no_docker)
    if not a.setup:
        serve()
