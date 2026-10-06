"""Neo4j driver for MITRE ATT&CK and incident attack graphs."""

from __future__ import annotations

from typing import Any

import structlog
from neo4j import GraphDatabase, Driver

from app.config import get_settings

logger = structlog.get_logger(__name__)

_driver: Driver | None = None


def connect() -> Driver:
    global _driver
    if _driver is None:
        settings = get_settings()
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def create_constraints() -> None:
    queries = [
        "CREATE CONSTRAINT technique_id IF NOT EXISTS FOR (t:Technique) REQUIRE t.id IS UNIQUE",
        "CREATE CONSTRAINT tactic_name IF NOT EXISTS FOR (t:Tactic) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT attacker_id IF NOT EXISTS FOR (a:Attacker) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT asset_id IF NOT EXISTS FOR (a:Asset) REQUIRE a.id IS UNIQUE",
        "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
    ]
    driver = connect()
    with driver.session() as session:
        for query in queries:
            session.run(query)


def add_technique(tech_id: str, name: str, description: str, tactic: str | None = None) -> None:
    driver = connect()
    with driver.session() as session:
        session.run(
            """
            MERGE (t:Technique {id: $id})
            SET t.name = $name, t.description = $description
            WITH t
            FOREACH (_ IN CASE WHEN $tactic IS NULL THEN [] ELSE [1] END |
              MERGE (ta:Tactic {name: $tactic})
              MERGE (t)-[:PART_OF]->(ta)
            )
            """,
            id=tech_id,
            name=name,
            description=description,
            tactic=tactic,
        )


def add_relationship(tech1_id: str, relation_type: str, tech2_id: str) -> None:
    allowed = {"SUBTECHNIQUE_OF", "RELATED_TO", "USES", "PART_OF"}
    rel = relation_type.upper() if relation_type.upper() in allowed else "RELATED_TO"
    driver = connect()
    with driver.session() as session:
        session.run(
            f"""
            MATCH (a:Technique {{id: $a}})
            MATCH (b:Technique {{id: $b}})
            MERGE (a)-[r:{rel}]->(b)
            """,
            a=tech1_id,
            b=tech2_id,
        )


def query_attack_graph(incident_id: int | None = None) -> dict[str, Any]:
    driver = connect()
    if incident_id is None:
        cypher = """
        MATCH (t:Technique)-[r]->(n)
        RETURN t.id AS sid, t.name AS sname, labels(t)[0] AS stype,
               type(r) AS rel, n.id AS tid, n.name AS tname, labels(n)[0] AS ttype
        LIMIT 400
        """
        params: dict[str, Any] = {}
    else:
        cypher = """
        MATCH (i:Incident {id: $incident_id})-[:HAS_ALERT]->(a:Attacker)-[r]->(n)
        RETURN a.id AS sid, a.name AS sname, labels(a)[0] AS stype,
               type(r) AS rel, n.id AS tid, n.name AS tname, labels(n)[0] AS ttype
        LIMIT 400
        """
        params = {"incident_id": incident_id}
    nodes: dict[str, dict[str, Any]] = {}
    links: list[dict[str, Any]] = []
    with driver.session() as session:
        for rec in session.run(cypher, **params):
            sid = rec["sid"] or rec["sname"]
            tid = rec["tid"] or rec["tname"]
            if sid:
                nodes[str(sid)] = {
                    "id": str(sid),
                    "name": rec["sname"] or str(sid),
                    "type": (rec["stype"] or "Technique").lower(),
                }
            if tid:
                nodes[str(tid)] = {
                    "id": str(tid),
                    "name": rec["tname"] or str(tid),
                    "type": (rec["ttype"] or "Technique").lower(),
                }
            if sid and tid:
                links.append({"source": str(sid), "target": str(tid), "relation": rec["rel"]})
    if not nodes:
        return _fallback_graph()
    return {"nodes": list(nodes.values()), "links": links}


def get_technique_details(technique_id: str) -> dict[str, Any]:
    driver = connect()
    with driver.session() as session:
        rec = session.run(
            """
            MATCH (t:Technique {id: $id})
            OPTIONAL MATCH (t)-[:PART_OF]->(ta:Tactic)
            OPTIONAL MATCH (t)-[r]-(other:Technique)
            RETURN t.id AS id, t.name AS name, t.description AS description,
                   collect(DISTINCT ta.name) AS tactics,
                   collect(DISTINCT {id: other.id, name: other.name, rel: type(r)}) AS related
            """,
            id=technique_id,
        ).single()
    if not rec:
        return {"id": technique_id, "name": technique_id, "description": "", "tactics": [], "related": []}
    return dict(rec)


def upsert_incident_graph(incident_id: int, src_ip: str, technique_id: str, dst_ip: str) -> None:
    driver = connect()
    with driver.session() as session:
        session.run(
            """
            MERGE (i:Incident {id: $incident_id})
            MERGE (att:Attacker {id: $src_ip})
            SET att.name = $src_ip
            MERGE (t:Technique {id: $technique_id})
            MERGE (asset:Asset {id: $dst_ip})
            SET asset.name = $dst_ip
            MERGE (i)-[:HAS_ALERT]->(att)
            MERGE (att)-[:USES]->(t)
            MERGE (t)-[:TARGETS]->(asset)
            """,
            incident_id=incident_id,
            src_ip=src_ip,
            technique_id=technique_id,
            dst_ip=dst_ip,
        )


def _fallback_graph() -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "192.168.1.100", "name": "192.168.1.100", "type": "attacker"},
            {"id": "T1046", "name": "Network Service Discovery", "type": "technique"},
            {"id": "TA0007", "name": "Discovery", "type": "tactic"},
            {"id": "10.0.0.5", "name": "10.0.0.5", "type": "asset"},
        ],
        "links": [
            {"source": "192.168.1.100", "target": "T1046", "relation": "USES"},
            {"source": "T1046", "target": "TA0007", "relation": "PART_OF"},
            {"source": "T1046", "target": "10.0.0.5", "relation": "TARGETS"},
        ],
    }


def ping() -> bool:
    driver = connect()
    with driver.session() as session:
        session.run("RETURN 1")
    return True
