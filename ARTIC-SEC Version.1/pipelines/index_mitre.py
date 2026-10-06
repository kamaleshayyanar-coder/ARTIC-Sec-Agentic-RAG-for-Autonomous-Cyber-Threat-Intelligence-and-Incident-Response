from __future__ import annotations

import json
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import get_settings
from app.db import neo4j as neo4j_db
from app.db import qdrant as qdrant_db
from app.rag.indexer import index_batch
from app.rag.retriever import register_bm25_corpus


def load_json(path: Path) -> list | dict:
    p = Path(path)
    if not p.exists():
        candidates = [
            Path("data/mitre-attack") / p.name,
            Path(__file__).resolve().parent.parent / "data" / "mitre-attack" / p.name,
        ]
        for c in candidates:
            if c.exists():
                p = c
                break
    with p.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    settings = get_settings()
    techniques = load_json(settings.mitre_techniques_path)
    tactics = load_json(settings.mitre_tactics_path) if settings.mitre_tactics_path.exists() else []
    relationships = (
        load_json(settings.mitre_relationships_path) if settings.mitre_relationships_path.exists() else []
    )
    if isinstance(techniques, dict):
        techniques = techniques.get("objects") or techniques.get("techniques") or []

    qdrant_db.create_collection()
    neo4j_db.create_constraints()

    documents = []
    for item in techniques:
        tech_id = item.get("id") or item.get("technique_id")
        name = item.get("name")
        description = item.get("description") or ""
        tactic = None
        kill_chain = item.get("kill_chain_phases") or []
        if kill_chain:
            tactic = kill_chain[0].get("phase_name")
        tactic = item.get("tactic") or tactic
        documents.append(
            {
                "id": tech_id,
                "technique_id": tech_id,
                "name": name,
                "text": f"{tech_id} {name}. {description}",
                "description": description,
                "tactic": tactic,
                "source": "mitre",
            }
        )

    count = index_batch(documents)
    register_bm25_corpus(documents)

    if isinstance(tactics, dict):
        tactics = tactics.get("tactics") or tactics.get("objects") or []
    for tactic in tactics:
        name = tactic.get("name") or tactic.get("id")
        if name:
            neo4j_db.add_technique(str(tactic.get("id") or name), str(name), tactic.get("description") or "", tactic=str(name))

    if isinstance(relationships, dict):
        relationships = relationships.get("relationships") or relationships.get("objects") or []
    for rel in relationships:
        source = rel.get("source") or rel.get("source_ref")
        target = rel.get("target") or rel.get("target_ref")
        rtype = rel.get("relationship_type") or rel.get("type") or "RELATED_TO"
        if source and target and str(source).startswith("T") and str(target).startswith("T"):
            neo4j_db.add_relationship(str(source), str(rtype), str(target))

    print(f"indexed_techniques={count}")


if __name__ == "__main__":
    main()
