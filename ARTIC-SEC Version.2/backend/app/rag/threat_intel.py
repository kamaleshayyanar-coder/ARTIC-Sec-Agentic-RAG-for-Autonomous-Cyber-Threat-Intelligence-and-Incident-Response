"""Live IP reputation lookups, layered on top of the static MITRE-only recon
that already existed. Degrades to a no-op (returns None) whenever:
  - THREAT_INTEL_ENABLED=false
  - the relevant API key is blank
  - the target IP is private/internal (nothing to look up externally)
  - the HTTP call fails or times out

so recon_agent.gather_intel() keeps working exactly as before in any
environment without keys configured -- this is additive enrichment, never a
hard dependency.
"""
from __future__ import annotations

import ipaddress
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


def _is_public_ip(value: str) -> bool:
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return False
    return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast)


def _cache_get(key: str) -> Any | None:
    try:
        from app.db.redis import cache_get

        return cache_get(key)
    except Exception:
        return None


def _cache_set(key: str, value: Any, ttl: int) -> None:
    try:
        from app.db.redis import cache_set

        cache_set(key, value, ttl)
    except Exception:
        pass


def _lookup_abuseipdb(ip: str, api_key: str, timeout: float) -> dict[str, Any] | None:
    try:
        resp = httpx.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": api_key, "Accept": "application/json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "source": "abuseipdb",
            "abuse_confidence_score": data.get("abuseConfidenceScore"),
            "country_code": data.get("countryCode"),
            "isp": data.get("isp"),
            "total_reports": data.get("totalReports"),
            "is_tor": data.get("isTor"),
        }
    except Exception as exc:
        logger.info("threat_intel.abuseipdb_unavailable", ip=ip, error=str(exc))
        return None


def _lookup_virustotal(ip: str, api_key: str, timeout: float) -> dict[str, Any] | None:
    try:
        resp = httpx.get(
            f"https://www.virustotal.com/api/v3/ip_addresses/{ip}",
            headers={"x-apikey": api_key},
            timeout=timeout,
        )
        resp.raise_for_status()
        stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        return {
            "source": "virustotal",
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
        }
    except Exception as exc:
        logger.info("threat_intel.virustotal_unavailable", ip=ip, error=str(exc))
        return None


def enrich_ip(ip: str) -> dict[str, Any] | None:
    """Returns combined external reputation for a public IP, or None if
    threat intel is disabled, unconfigured, the IP is internal, or every
    configured provider failed/timed out."""
    settings = get_settings()
    if not settings.threat_intel_enabled or not _is_public_ip(ip):
        return None

    cache_key = f"threat_intel:{ip}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    providers: dict[str, dict[str, Any] | None] = {}
    if settings.abuseipdb_api_key:
        providers["abuseipdb"] = _lookup_abuseipdb(ip, settings.abuseipdb_api_key, settings.threat_intel_timeout_seconds)
    if settings.virustotal_api_key:
        providers["virustotal"] = _lookup_virustotal(ip, settings.virustotal_api_key, settings.threat_intel_timeout_seconds)

    results = {k: v for k, v in providers.items() if v is not None}
    if not results:
        return None

    malicious_signal = False
    if "abuseipdb" in results and (results["abuseipdb"].get("abuse_confidence_score") or 0) >= 50:
        malicious_signal = True
    if "virustotal" in results and (results["virustotal"].get("malicious") or 0) > 0:
        malicious_signal = True

    payload = {"ip": ip, "providers": results, "malicious_signal": malicious_signal}
    _cache_set(cache_key, payload, settings.threat_intel_cache_ttl_seconds)
    return payload
