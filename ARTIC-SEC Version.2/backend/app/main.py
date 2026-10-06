"""FastAPI entrypoint: REST, SSE, WebSocket, background ingest."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.core.exceptions import ArticSecError
from app.core.kafka_consumer import ingestor
from app.core.logging import configure_logging, get_logger
from app.core.websocket_manager import manager
from app.db.postgres import create_tables, run_migrations

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings.debug)
    create_tables()
    run_migrations()
    try:
        from app.db import neo4j as neo4j_db
        from app.db import qdrant as qdrant_db

        neo4j_db.create_constraints()
        qdrant_db.create_collection()
    except Exception as exc:
        logger.warning("optional_store_init_failed", error=str(exc))
    await ingestor.start()
    logger.info("app.startup", env=settings.app_env)
    yield
    await ingestor.stop()
    try:
        from app.db.neo4j import close as neo4j_close

        neo4j_close()
    except Exception:
        pass
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Agentic real-time intelligent cybersecurity platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(ArticSecError)
async def artic_error_handler(_, exc: ArticSecError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "detail": exc.detail, "status_code": exc.status_code},
    )


@app.get("/health")
def health() -> dict:
    checks: dict[str, str] = {"api": "ok"}
    try:
        from app.db.postgres import ping as pg_ping

        pg_ping()
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error:{exc}"
    return {"status": "ok" if checks.get("postgres") == "ok" else "degraded", "version": __version__, "checks": checks}


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "version": __version__, "docs": "/docs"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        await manager.send_personal({"event": "hello", "clients": manager.client_count}, websocket)
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await manager.send_personal({"event": "pong"}, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
