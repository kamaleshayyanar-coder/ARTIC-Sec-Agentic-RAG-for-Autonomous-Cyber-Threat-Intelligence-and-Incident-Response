"""Knowledge-graph helpers wrapping Neo4j MITRE schema."""

from __future__ import annotations

from typing import Any

from app.db import neo4j as neo4j_db


def create_schema() -> None:
    neo4j_db.create_constraints()


def add_technique(technique_id: str, name: str, description: str, tactic: str | None = None) -> None:
    neo4j_db.add_technique(technique_id, name, description, tactic=tactic)


def add_relationship(tech1_id: str, relation_type: str, tech2_id: str) -> None:
    neo4j_db.add_relationship(tech1_id, relation_type, tech2_id)


def get_technique_details(technique_id: str) -> dict[str, Any]:
    return neo4j_db.get_technique_details(technique_id)


def get_attack_graph(incident_id: int | None = None) -> dict[str, Any]:
    return neo4j_db.query_attack_graph(incident_id)
