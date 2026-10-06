"""NIST SP 800-61 aligned incident report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json
import re


NIST_SECTIONS = (
    "Executive Summary",
    "Timeline",
    "Attack Details",
    "Impact",
    "Response",
    "Recommendations",
    "Indicators of Compromise",
)


def extract_iocs(incident: dict[str, Any]) -> dict[str, list[str]]:
    alerts = incident.get("alerts") or []
    ips = sorted({a.get("src_ip") for a in alerts if a.get("src_ip")} | {a.get("dst_ip") for a in alerts if a.get("dst_ip")})
    techniques = sorted({a.get("mitre_technique") for a in alerts if a.get("mitre_technique")})
    blob = json.dumps(incident, default=str)
    domains = sorted(set(re.findall(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", blob, flags=re.I)))
    hashes = sorted(set(re.findall(r"\b[a-fA-F0-9]{32,64}\b", blob)))
    return {
        "ips": [ip for ip in ips if ip],
        "domains": domains[:20],
        "hashes": hashes[:20],
        "mitre_techniques": [t for t in techniques if t],
    }


def summarize_for_executive(incident: dict[str, Any]) -> str:
    title = incident.get("title") or "Security incident"
    severity = incident.get("severity") or "medium"
    decision = incident.get("decision") or {}
    return (
        f"{title} was classified as {severity} severity. "
        f"Primary recommended action is {decision.get('primary_action', 'MONITOR')}. "
        "Business impact should be reviewed by the asset owner within the current shift."
    )


def generate_report(incident: dict[str, Any]) -> dict[str, Any]:
    iocs = extract_iocs(incident)
    analysis = incident.get("analysis") or {}
    decision = incident.get("decision") or {}
    now = datetime.now(timezone.utc).isoformat()
    markdown = f"""# Incident Report (NIST SP 800-61)

## Executive Summary
{summarize_for_executive(incident)}

## Timeline
- Detected: {incident.get('created_at') or now}
- Last update: {now}
- Status: {incident.get('status') or 'open'}

## Attack Details
- Hypothesis: {analysis.get('hypothesis')}
- Root cause: {analysis.get('root_cause')}
- TTPs: {', '.join(analysis.get('ttps') or iocs['mitre_techniques'] or ['Unknown'])}
- Goal: {analysis.get('attack_goal')}

## Impact
Risk score {decision.get('risk_score', incident.get('risk_score', 'n/a'))}. Affected assets listed in IOCs.

## Response
- Primary: {decision.get('primary_action')}
- Secondary: {', '.join(decision.get('secondary_actions') or [])}
- Human approval required: {decision.get('requires_approval')}
- Guardrail: {incident.get('guardrail')}

## Recommendations
1. Confirm containment on the source IP and review firewall policy.
2. Hunt for related TTPs in the same /24 and identity systems.
3. Update detection content for the mapped MITRE techniques.

## Indicators of Compromise
```json
{json.dumps(iocs, indent=2)}
```
"""
    return {
        "markdown": markdown,
        "json": {
            "title": incident.get("title"),
            "severity": incident.get("severity"),
            "executive_summary": summarize_for_executive(incident),
            "iocs": iocs,
            "decision": decision,
            "analysis": analysis,
            "generated_at": now,
            "standard": "NIST SP 800-61r2",
        },
        "sections": list(NIST_SECTIONS),
    }
