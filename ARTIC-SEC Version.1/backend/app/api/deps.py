"""FastAPI dependencies: DB sessions, clients, optional JWT."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated, Any, Optional

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.db.models.user import User
from app.db.postgres import SessionLocal


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_settings_dep() -> Settings:
    return get_settings()


def get_neo4j():
    from app.db import neo4j as neo4j_mod

    return neo4j_mod


def get_qdrant():
    from app.db import qdrant as qdrant_mod

    return qdrant_mod


def get_redis():
    from app.db import redis as redis_mod

    return redis_mod


def verify_token(authorization: Annotated[Optional[str], Header()] = None) -> dict[str, Any]:
    settings = get_settings()
    if not settings.auth_enabled:
        return {"sub": "anonymous", "role": "analyst"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid token") from exc


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[dict[str, Any], Depends(verify_token)],
) -> Optional[User]:
    settings = get_settings()
    if not settings.auth_enabled:
        return None
    username = token.get("sub")
    user = db.query(User).filter(User.username == username).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(user: Annotated[Optional[User], Depends(get_current_user)]) -> Optional[User]:
    settings = get_settings()
    if not settings.auth_enabled:
        return user
    if user is None or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[Optional[User], Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
