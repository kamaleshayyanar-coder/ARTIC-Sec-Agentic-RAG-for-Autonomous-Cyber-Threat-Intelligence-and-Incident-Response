from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.core.auth import ROLES


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    # Self-service registration can only ever create the lowest-privilege
    # role; promoting someone to approver/admin is an admin-only action
    # (see PATCH /auth/users/{id}/role), never something a signup form sets.
    role: str = "analyst"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str | None = None


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description=f"one of: {', '.join(ROLES)}")
