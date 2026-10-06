"""Executes approved SOAR actions.

This is intentionally a *simulated* connector layer: it never touches real
network infrastructure. Each executor returns a structured result recording
what it *would* have done, which is exactly what a real firewall/EDR/IdP
connector implementation would need to replace (swap the body of each
`_exec_*` function for a real API call; the guardrail/approval/audit layers
around it don't need to change).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import httpx
import structlog

from app.config import get_settings
from app.core.security import audit_log_action

logger = structlog.get_logger(__name__)


def _exec_block_ip(target: str) -> dict[str, Any]:
    return {"connector": "firewall.block_ip", "target": target, "effect": "denied inbound/outbound on all interfaces"}


def _exec_isolate_host(target: str) -> dict[str, Any]:
    return {"connector": "edr.isolate_host", "target": target, "effect": "host moved to quarantine VLAN"}


def _exec_disable_account(target: str) -> dict[str, Any]:
    return {"connector": "idp.disable_account", "target": target, "effect": "account disabled, sessions revoked"}


def _exec_revoke_credentials(target: str) -> dict[str, Any]:
    return {"connector": "idp.revoke_credentials", "target": target, "effect": "tokens/keys revoked"}


def _exec_quarantine_file(target: str) -> dict[str, Any]:
    return {"connector": "edr.quarantine_file", "target": target, "effect": "file moved to quarantine store"}


def _exec_rate_limit(target: str) -> dict[str, Any]:
    return {"connector": "waf.rate_limit", "target": target, "effect": "rate limit applied (100 req/min)"}


def _exec_monitor(target: str) -> dict[str, Any]:
    return {"connector": "siem.watchlist", "target": target, "effect": "added to active watchlist, no containment action taken"}


def _exec_escalate(target: str) -> dict[str, Any]:
    return {"connector": "soc.escalate", "target": target, "effect": "escalated to on-call incident commander"}


EXECUTORS: dict[str, Callable[[str], dict[str, Any]]] = {
    "BLOCK_IP": _exec_block_ip,
    "ISOLATE_HOST": _exec_isolate_host,
    "DISABLE_ACCOUNT": _exec_disable_account,
    "REVOKE_CREDENTIALS": _exec_revoke_credentials,
    "QUARANTINE_FILE": _exec_quarantine_file,
    "RATE_LIMIT": _exec_rate_limit,
    "MONITOR": _exec_monitor,
    "ESCALATE": _exec_escalate,
}


def execute(action_type: str, target: str) -> dict[str, Any]:
    action_type = action_type.upper()
    executor = EXECUTORS.get(action_type)
    if executor is None:
        return {"status": "failed", "error": f"no executor registered for {action_type}"}
    try:
        result = executor(target)
        result["status"] = "executed"
        result["ts"] = datetime.now(timezone.utc).isoformat()
        return result
    except Exception as exc:  # never let a bad connector implementation crash the API
        logger.error("playbook.execute_failed", action_type=action_type, target=target, error=str(exc))
        return {"status": "failed", "error": str(exc)}


def notify_slack(text: str) -> bool:
    """Best-effort Slack webhook post. No-ops (returns False) if unconfigured
    or unreachable -- action execution must never depend on Slack being up."""
    settings = get_settings()
    if not settings.slack_webhook_url:
        return False
    try:
        resp = httpx.post(settings.slack_webhook_url, json={"text": text}, timeout=3.0)
        return resp.status_code < 300
    except Exception as exc:
        logger.warning("playbook.slack_notify_failed", error=str(exc))
        return False


def run_and_audit(action_type: str, target: str, *, agent_id: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    result = execute(action_type, target)
    audit_log_action({"type": action_type, "target": target, **(extra or {})}, result, agent_id=agent_id)
    if result.get("status") == "executed":
        notify_slack(f":shield: ARTIC-Sec executed *{action_type}* on `{target}` (agent={agent_id})")
    return result
