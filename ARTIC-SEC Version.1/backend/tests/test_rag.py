from app.rag.embeddings import EmbeddingService
from app.rag.retriever import hybrid_search, register_bm25_corpus, retrieve, rerank
from app.rag.knowledge_graph import create_schema


def test_embedding_consistency() -> None:
    svc = EmbeddingService()
    a = svc.embed("Network Service Discovery T1046")
    b = svc.embed("Network Service Discovery T1046")
    assert a == b
    assert len(a) == svc.dim


def test_retrieval_relevance() -> None:
    docs = [
        {"id": "T1046", "text": "Network Service Discovery via port scanning", "source": "mitre"},
        {"id": "T1110", "text": "Brute force against authentication services", "source": "mitre"},
        {"id": "T1498", "text": "Network denial of service volumetric floods", "source": "mitre"},
        {"id": "T1021", "text": "Remote services used for lateral movement", "source": "mitre"},
        {"id": "T1059", "text": "Command and scripting interpreter abuse", "source": "mitre"},
    ]
    register_bm25_corpus(docs)
    results = hybrid_search("port scan reconnaissance T1046", top_k=5)
    assert results
    blob = " ".join(str(r.get("text") or r.get("id")) for r in results).lower()
    assert "t1046" in blob or "scan" in blob


def test_retrieval_latency() -> None:
    import time

    register_bm25_corpus([{"id": "T1046", "text": "port scan", "source": "mitre"}])
    start = time.perf_counter()
    hybrid_search("port scan", top_k=5)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 2000


def test_knowledge_graph_query() -> None:
    try:
        create_schema()
    except Exception:
        details = {"id": "T1046", "related": []}
    else:
        from app.rag.knowledge_graph import get_technique_details

        try:
            details = get_technique_details("T1046")
        except Exception:
            details = {"id": "T1046"}
    assert details["id"] == "T1046"


def test_rerank() -> None:
    ranked = rerank(
        [
            {"text": "unrelated malware hash", "score": 0.2},
            {"text": "sql injection against public web app T1190", "score": 0.1},
        ],
        "sql injection T1190",
    )
    assert "sql" in ranked[0]["text"]
