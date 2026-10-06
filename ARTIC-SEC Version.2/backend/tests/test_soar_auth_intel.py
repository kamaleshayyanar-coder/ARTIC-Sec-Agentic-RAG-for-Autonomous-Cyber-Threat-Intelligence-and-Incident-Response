"""Tests for the SOAR playbooks, auth/RBAC, and threat-intel additions."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents import playbook_executor
from app.api.deps import get_db
from app.core.auth import create_access_token, hash_password, verify_password
import app.db.models  # noqa: F401  (register tables)
from app.db.postgres import Base
from app.main import app as fastapi_app
from app.rag.threat_intel import _is_public_ip, enrich_ip


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_db
    yield TestClient(fastapi_app)  # no `with`: skip lifespan (Neo4j/Qdrant not needed)
    fastapi_app.dependency_overrides.clear()


def test_password_hash_roundtrip():
    hashed = hash_password("s3cretpass")
    assert hashed != "s3cretpass"
    assert verify_password("s3cretpass", hashed)
    assert not verify_password("wrong", hashed)


def test_token_contains_role():
    from jose import jwt
    from app.config import get_settings

    s = get_settings()
    tok = create_access_token("bob", "approver")
    claims = jwt.decode(tok, s.secret_key, algorithms=[s.jwt_algorithm])
    assert claims["sub"] == "bob" and claims["role"] == "approver"


def test_register_login_me(client):
    r = client.post("/api/v1/auth/register", json={"username": "alice", "email": "a@x.io", "password": "password123"})
    assert r.status_code == 201 and r.json()["role"] == "analyst"
    assert client.post("/api/v1/auth/login", json={"username": "alice", "password": "password123"}).status_code == 200
    assert client.post("/api/v1/auth/login", json={"username": "alice", "password": "nope"}).status_code == 401
    dup = client.post("/api/v1/auth/register", json={"username": "alice", "email": "b@x.io", "password": "password123"})
    assert dup.status_code == 409


def test_self_registration_cannot_escalate_role(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": "mallory", "email": "m@x.io", "password": "password123", "role": "admin"},
    )
    assert r.json()["role"] == "analyst"


def test_rbac_blocks_analyst_when_auth_enabled(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "auth_enabled", True)
    client.post("/api/v1/auth/register", json={"username": "alice", "email": "a@x.io", "password": "password123"})
    tok = client.post("/api/v1/auth/login", json={"username": "alice", "password": "password123"}).json()["access_token"]
    r = client.post("/api/v1/actions/1/approve", json={}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_propose_approve_flow(client):
    alert = client.post(
        "/api/v1/alerts",
        json={"type": "PortScan", "src_ip": "203.0.113.44", "dst_ip": "10.0.0.5", "risk_score": 0.81, "severity": "high"},
    ).json()
    action = client.post(f"/api/v1/actions/propose/{alert['id']}").json()
    assert action["status"] == "pending_approval"
    done = client.post(f"/api/v1/actions/{action['id']}/approve", json={"note": "ok"}).json()
    assert done["status"] == "executed"
    assert client.post(f"/api/v1/actions/{action['id']}/reject", json={}).status_code == 409


def test_reject_flow(client):
    alert = client.post(
        "/api/v1/alerts",
        json={"type": "DDoS", "src_ip": "198.51.100.7", "dst_ip": "10.0.0.9", "risk_score": 0.9, "severity": "critical"},
    ).json()
    action = client.post(f"/api/v1/actions/propose/{alert['id']}").json()
    rej = client.post(f"/api/v1/actions/{action['id']}/reject", json={"note": "false positive"}).json()
    assert rej["status"] == "rejected"


def test_executor_unknown_action():
    assert playbook_executor.execute("NUKE_FROM_ORBIT", "x")["status"] == "failed"
    assert playbook_executor.execute("block_ip", "1.2.3.4")["status"] == "executed"


def test_threat_intel_skips_private_and_unconfigured():
    assert not _is_public_ip("10.0.0.5") and _is_public_ip("8.8.8.8")
    assert enrich_ip("10.0.0.5") is None
    assert enrich_ip("8.8.8.8") is None  # no API keys configured -> graceful no-op
