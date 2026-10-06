"""Dedicated guardrail agent wrapping core.security."""

from __future__ import annotations

from typing import Any

from app.core.security import (
    audit_log_action,
    detect_prompt_injection,
    get_audit_trail,
    guardrail_check,
    require_safe_action,
)


def validate_action(action: dict[str, Any], *, agent_id: str = "response") -> dict[str, Any]:
    result = guardrail_check(action, agent_id=agent_id)
    return {
        "allowed": result.allowed,
        "reasons": result.reasons,
        "action": result.action,
        "payload": result.sanitized_payload,
    }


def detect_adversarial_intent(prompt: str) -> dict[str, Any]:
    return detect_prompt_injection(prompt)


def rate_limit_check(agent_id: str) -> dict[str, Any]:
    probe = guardrail_check({"type": "MONITOR"}, agent_id=agent_id)
    return {"allowed": "rate_limited" not in probe.reasons, "reasons": probe.reasons}


def audit_trail(action: dict[str, Any], result: dict[str, Any], *, agent_id: str = "guardrail") -> None:
    audit_log_action(action, result, agent_id=agent_id)


def latest_audit(limit: int = 50) -> list[dict[str, Any]]:
    return get_audit_trail(limit)


__all__ = [
    "validate_action",
    "detect_adversarial_intent",
    "rate_limit_check",
    "audit_trail",
    "require_safe_action",
    "latest_audit",
]
