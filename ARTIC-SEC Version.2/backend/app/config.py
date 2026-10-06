"""Typed runtime configuration loaded from environment / .env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "ARTIC-Sec"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = Field(default="dev-only-change-me", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    auth_enabled: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/articsec"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "changeme"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "mitre_attack"
    redis_url: str = "redis://localhost:6379/0"

    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_alert_topic: str = "security-alerts"
    kafka_group_id: str = "articsec-consumers"

    llm_model: str = "llama3.2:3b"
    llm_base_url: str = "http://localhost:11434"
    llm_timeout_seconds: float = 60.0
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    cors_origins: str = "http://localhost:3000"
    ws_heartbeat_seconds: int = 30
    alert_stream_interval_seconds: float = 2.0
    max_actions_per_hour: int = 10

    # --- Auth / RBAC ---
    access_token_expire_minutes: int = 480

    # --- SOAR playbooks ---
    auto_execute_low_risk: bool = True
    slack_webhook_url: str = ""

    # --- Live threat intelligence enrichment ---
    abuseipdb_api_key: str = ""
    virustotal_api_key: str = ""
    threat_intel_enabled: bool = True
    threat_intel_cache_ttl_seconds: int = 3600
    threat_intel_timeout_seconds: float = 3.0

    synthetic_alerts_path: Path = Path("../data/synthetic/synthetic_alerts.csv")
    mitre_techniques_path: Path = Path("../data/mitre-attack/mitre_techniques.json")
    mitre_tactics_path: Path = Path("../data/mitre-attack/mitre_tactics.json")
    mitre_relationships_path: Path = Path("../data/mitre-attack/mitre_relationships.json")
    cic_data_dir: Path = Path("../data/cic-ids2017")
    model_dir: Path = Path("app/ml/models")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _origins_str(cls, value: object) -> str:
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
