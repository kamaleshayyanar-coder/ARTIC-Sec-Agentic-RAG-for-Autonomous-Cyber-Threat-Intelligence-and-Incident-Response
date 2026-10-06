"""Registration, login, and RBAC role management.

Auth is OFF by default (AUTH_ENABLED=false in .env), matching the rest of
the demo app -- api.deps.verify_token/get_current_user already short-circuit
to an anonymous "analyst" when it's off, so nothing here breaks the no-auth
quick start. Set AUTH_ENABLED=true to require real login for the endpoints
that check CurrentUser / require_role(...) (see api/v1/actions.py).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from fastapi import Depends

from app.api.deps import CurrentUser, DbSession, require_role
from app.core.auth import ROLES, create_access_token, hash_password, verify_password
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RoleUpdateRequest, TokenResponse, UserOut

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    exists = db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if exists:
        raise HTTPException(status_code=409, detail="username or email already registered")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="analyst",  # see RegisterRequest docstring: self-signup is always lowest privilege
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.username, user.role)
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    from datetime import datetime, timezone

    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(user.username, user.role)
    return TokenResponse(access_token=token, role=user.role, username=user.username)


@router.get("/me", response_model=UserOut)
def me(current: CurrentUser) -> UserOut:
    if current is None:
        # AUTH_ENABLED=false path: verify_token/get_current_user return an
        # anonymous analyst rather than a real row.
        return UserOut(id=0, username="anonymous", email="anonymous@local", role="analyst")
    return UserOut(**current.to_dict())


@router.get("/users", response_model=list[UserOut])
def list_users(db: DbSession, _: object = Depends(require_role("approver", "admin"))) -> list[UserOut]:
    rows = db.scalars(select(User).order_by(User.id)).all()
    return [UserOut(**row.to_dict()) for row in rows]


@router.patch("/users/{user_id}/role", response_model=UserOut)
def set_role(
    user_id: int, payload: RoleUpdateRequest, db: DbSession, _: object = Depends(require_role("admin"))
) -> UserOut:
    if payload.role not in ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {ROLES}")
    row = db.get(User, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="user not found")
    row.role = payload.role
    db.commit()
    db.refresh(row)
    return UserOut(**row.to_dict())
