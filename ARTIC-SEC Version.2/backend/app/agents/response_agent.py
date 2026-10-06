"""Containment decisioning with human-approval policy."""

from __future__ import annotations

from typing import Any

SEVERITY_WEIGHT = {"low": 0.25, "medium": 0.5, "high": 0.8, "critical": 1.0}
CRITICAL_ASSETS = {"10.0.0.1", "10.0.0.5", "dc01", "jumpbox"}


def assess_risk(alert: dict[str, Any], analysis: dict[str, Any]) -> float:
    sev = str(analysis.get("severity") or alert.get("severity") or "medium").lower()
    confidence = float(analysis.get("confidence") or alert.get("risk_score") or 0.5)
    asset = 1.0 if str(alert.get("dst_ip")) in CRITICAL_ASSETS else 0.6
    anomaly = float(alert.get("anomaly_score") or 0.0)
    score = 0.4 * SEVERITY_WEIGHT.get(sev, 0.5) + 0.3 * confidence + 0.2 * asset + 0.1 * anomaly
    return round(min(1.0, max(0.0, score)), 4)


def requires_human_approval(decision: dict[str, Any]) -> bool:
    action = str(decision.get("primary_action") or "").upper()
    severity = str(decision.get("severity") or "medium").lower()
    if severity in {"high", "critical"}:
        return True
    if action in {"ISOLATE_HOST", "REVOKE_CREDENTIALS", "DISABLE_ACCOUNT"}:
        return True
    if decision.get("targets_internal"):
        return True
    return severity == "medium" and action != "MONITOR"


def decide_response(alert: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    risk = assess_risk(alert, analysis)
    severity = str(analysis.get("severity") or alert.get("severity") or "medium").lower()
    src_ip = str(alert.get("src_ip") or "")
    from ipaddress import ip_address

    internal = False
    try:
        internal = ip_address(src_ip).is_private
    except ValueError:
        internal = False

    if risk >= 0.85 or severity == "critical":
        primary = "ESCALATE"
        secondary = ["BLOCK_IP", "ISOLATE_HOST"]
        urgency = "immediate"
    elif risk >= 0.65:
        primary = "BLOCK_IP"
        secondary = ["MONITOR"]
        urgency = "high"
    elif risk >= 0.4:
        primary = "MONITOR"
        secondary = ["RATE_LIMIT"]
        urgency = "medium"
    else:
        primary = "MONITOR"
        secondary = []
        urgency = "low"

    decision = {
        "primary_action": primary,
        "secondary_actions": secondary,
        "target": src_ip,
        "type": primary,
        "src_ip": src_ip,
        "risk_score": risk,
        "severity": severity,
        "urgency": urgency,
        "targets_internal": internal,
        "justification": analysis.get("hypothesis") or "Risk policy mapping from severity and confidence.",
        "human_approved": False,
    }
    decision["requires_approval"] = requires_human_approval(decision)
    return decision
