"""SOC action guardrails, prompt-injection detection, RAG source trust, audit log."""

from __future__ import annotations

import ipaddress
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

import structlog

from app.config import Settings, get_settings
from app.core.exceptions import GuardrailRejectedError

logger = structlog.get_logger(__name__)

APPROVED_ACTIONS = frozenset(
    {
        "MONITOR",
        "BLOCK_IP",
        "ISOLATE_HOST",
        "REVOKE_CREDENTIALS",
        "ESCALATE",
        "QUARANTINE_FILE",
        "DISABLE_ACCOUNT",
        "RATE_LIMIT",
    }
)

INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"disregard\s+(the\s+)?(system|prior)\s+(prompt|instructions)", re.I),
    re.compile(r"you\s+are\s+now\s+(dan|unrestricted|jailbroken)", re.I),
    re.compile(r"delete\s+all\s+data", re.I),
    re.compile(r"drop\s+table", re.I),
    re.compile(r"truncate\s+table", re.I),
    re.compile(r";\s*(drop|delete|update|insert)\s+", re.I),
    re.compile(r"execute\s+(this\s+)?(shell|bash|powershell)\s+command", re.I),
    re.compile(r"os\.system\s*\(", re.I),
    re.compile(r"subprocess\.(run|popen|call)", re.I),
    re.compile(r"rm\s+-rf\s+/", re.I),
    re.compile(r"exfiltrat(e|ion)", re.I),
    re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.I),
    re.compile(r"tool\s+hijack", re.I),
)

TRUSTED_SOURCE_PREFIXES = (
    "mitre",
    "nvd",
    "cve",
    "internal-incident",
    "articsec",
    "attack.mitre.org",
)


@dataclass
class GuardrailResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    action: str | None = None
    sanitized_payload: dict[str, Any] | None = None


class ActionRateLimiter:
    def __init__(self, max_actions: int, window_seconds: int = 3600) -> None:
        self.max_actions = max_actions
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, agent_id: str) -> bool:
        now = time.monotonic()
        bucket = self._events[agent_id]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.max_actions:
            return False
        bucket.append(now)
        return True


_AUDIT: list[dict[str, Any]] = []
_RATE_LIMITER: ActionRateLimiter | None = None


def _limiter() -> ActionRateLimiter:
    global _RATE_LIMITER
    if _RATE_LIMITER is None:
        settings = get_settings()
        _RATE_LIMITER = ActionRateLimiter(settings.max_actions_per_hour)
    return _RATE_LIMITER


def detect_prompt_injection(text: str) -> dict[str, Any]:
    if not text:
        return {"detected": False, "matches": [], "score": 0.0}
    matches = [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]
    semantic_score = min(1.0, 0.25 * len(matches))
    if "ignore" in text.lower() and "instruction" in text.lower():
        semantic_score = max(semantic_score, 0.7)
        if "ignore previous instructions" not in " ".join(matches).lower():
            matches.append("semantic:instruction_override")
    detected = bool(matches) or semantic_score >= 0.5
    return {"detected": detected, "matches": matches, "score": round(semantic_score, 3)}


def validate_rag_source(source: str) -> bool:
    if not source:
        return False
    normalized = source.strip().lower()
    return any(normalized.startswith(prefix) or prefix in normalized for prefix in TRUSTED_SOURCE_PREFIXES)


def _is_internal_ip(value: str) -> bool:
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return False
    return bool(addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)


def guardrail_check(action: dict[str, Any] | str, *, agent_id: str = "response") -> GuardrailResult:
    if isinstance(action, str):
        action = {"type": action}
    action_type = str(action.get("type") or action.get("primary_action") or "").upper()
    reasons: list[str] = []
    if action_type not in APPROVED_ACTIONS:
        reasons.append(f"action_not_approved:{action_type or 'MISSING'}")
    target = str(action.get("target") or action.get("src_ip") or action.get("dst_ip") or "")
    if action_type in {"BLOCK_IP", "ISOLATE_HOST"} and target and _is_internal_ip(target):
        if not action.get("human_approved"):
            reasons.append("internal_ip_requires_human_approval")
    payload_text = json_dumps(action)
    injection = detect_prompt_injection(payload_text)
    if injection["detected"]:
        reasons.append("prompt_injection")
    if not _limiter().allow(agent_id):
        reasons.append("rate_limited")
    allowed = not reasons
    result = GuardrailResult(
        allowed=allowed,
        reasons=reasons,
        action=action_type,
        sanitized_payload={k: v for k, v in action.items() if k != "raw_prompt"},
    )
    audit_log_action(action, {"allowed": allowed, "reasons": reasons}, agent_id=agent_id)
    if not allowed:
        logger.warning("guardrail.rejected", action=action_type, reasons=reasons, agent_id=agent_id)
    return result


def require_safe_action(action: dict[str, Any], *, agent_id: str = "response") -> dict[str, Any]:
    result = guardrail_check(action, agent_id=agent_id)
    if not result.allowed:
        raise GuardrailRejectedError("Action blocked by guardrails", detail=";".join(result.reasons))
    return result.sanitized_payload or action


def audit_log_action(action: dict[str, Any] | str, result: dict[str, Any], *, agent_id: str = "system") -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "action": action if isinstance(action, dict) else {"type": action},
        "result": result,
    }
    _AUDIT.append(record)
    if len(_AUDIT) > 10_000:
        del _AUDIT[:5000]
    logger.info("audit.action", **{k: record[k] for k in ("ts", "agent_id")})


def get_audit_trail(limit: int = 100) -> list[dict[str, Any]]:
    return list(_AUDIT[-limit:])


def json_dumps(payload: Any) -> str:
    try:
        import json

        return json.dumps(payload, default=str)
    except Exception:
        return str(payload)


def scan_documents(documents: Iterable[dict[str, Any]]) -> list[str]:
    poisoned: list[str] = []
    for doc in documents:
        text = str(doc.get("text") or doc.get("content") or "")
        source = str(doc.get("source") or "")
        if detect_prompt_injection(text)["detected"] or not validate_rag_source(source):
            poisoned.append(str(doc.get("id") or source or "unknown"))
    return poisoned
