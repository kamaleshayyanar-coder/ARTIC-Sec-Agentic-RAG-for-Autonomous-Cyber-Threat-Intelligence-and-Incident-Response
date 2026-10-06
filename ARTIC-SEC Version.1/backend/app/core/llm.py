"""Ollama-compatible LLM client with deterministic fallback."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx
import structlog

from app.config import Settings, get_settings

logger = structlog.get_logger(__name__)


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def generate(self, prompt: str, *, json_mode: bool = True, system: str | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "prompt": prompt if not system else f"{system}\n\n{prompt}",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 1024},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(f"{self.settings.llm_base_url.rstrip('/')}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return str(data.get("response", "")).strip()
        except Exception as exc:
            logger.warning("llm.unavailable", error=str(exc))
            return self._fallback(prompt, json_mode=json_mode)

    async def stream(self, prompt: str, *, system: str | None = None) -> AsyncIterator[str]:
        payload = {
            "model": self.settings.llm_model,
            "prompt": prompt if not system else f"{system}\n\n{prompt}",
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                async with client.stream(
                    "POST", f"{self.settings.llm_base_url.rstrip('/')}/api/generate", json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
        except Exception as exc:
            logger.warning("llm.stream_unavailable", error=str(exc))
            fallback = self._fallback(prompt, json_mode=False)
            for word in fallback.split(" "):
                yield word + " "

    @staticmethod
    def _fallback(prompt: str, *, json_mode: bool) -> str:
        lowered = prompt.lower()
        attack = "PortScan"
        for label in ("ddos", "sqli", "sql injection", "bruteforce", "xss", "infiltration", "bot"):
            if label in lowered:
                attack = label.upper() if label != "sql injection" else "SQLi"
                break
        if json_mode:
            return json.dumps(
                {
                    "severity": "high",
                    "confidence": 0.72,
                    "attack_goal": "reconnaissance_or_initial_access",
                    "ttps": ["T1046"],
                    "hypothesis": f"Fallback analyst: traffic pattern consistent with {attack}.",
                    "root_cause": "Automated scan or exploitation attempt against exposed service.",
                }
            )
        return (
            f"Fallback SOC insight: observed activity resembles {attack}. "
            "Correlate source IP history, map to MITRE T1046/T1190, and apply least-privilege containment."
        )
