"""PostgreSQL engine, session factory, and schema bootstrap."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine_kwargs = {"pool_pre_ping": True, "future": True}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update({"pool_size": 10, "max_overflow": 20})
else:
    from sqlalchemy.pool import StaticPool
    engine_kwargs.update({"connect_args": {"check_same_thread": False}, "poolclass": StaticPool})

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    global engine, SessionLocal
    from app.db import models  # noqa: F401

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        # Fallback to zero-dependency local SQLite
        from sqlalchemy.pool import StaticPool
        sqlite_url = "sqlite:///articsec.db"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """Lightweight additive migrations when Alembic is not wired yet."""
    statements = [
        "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS reasoning_json TEXT",
        "ALTER TABLE incidents ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(128)",
        "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS payload_json TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ",
    ]
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception:
                continue


def ping() -> bool:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
