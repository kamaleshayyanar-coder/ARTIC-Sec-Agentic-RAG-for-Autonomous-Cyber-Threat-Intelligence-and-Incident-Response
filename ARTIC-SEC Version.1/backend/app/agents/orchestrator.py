"""LangGraph incident-response orchestrator."""

from __future__ import annotations

from typing import Any, AsyncIterator, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.agents.analysis_agent import analyze, correlate
from app.agents.guardrail_agent import validate_action
from app.agents.recon_agent import enrich_alert, gather_intel
from app.agents.report_agent import generate_report
from app.agents.response_agent import decide_response

logger = structlog.get_logger(__name__)


class AgentState(TypedDict, total=False):
    alert: dict[str, Any]
    classification: dict[str, Any]
    evidence: dict[str, Any]
    analysis: dict[str, Any]
    decision: dict[str, Any]
    guardrail: dict[str, Any]
    execution: dict[str, Any]
    report: dict[str, Any]
    steps: list[dict[str, Any]]
    db: Any


def _step(state: AgentState, name: str, status: str, output: Any) -> None:
    steps = list(state.get("steps") or [])
    steps.append({"step": name, "status": status, "output": output})
    state["steps"] = steps


def classify_node(state: AgentState) -> AgentState:
    alert = state["alert"]
    classification = {
        "type": alert.get("ml_prediction") or alert.get("type"),
        "severity": alert.get("severity"),
        "risk_score": alert.get("risk_score"),
    }
    state["classification"] = classification
    _step(state, "classify", "completed", classification)
    return state


def investigate_node(state: AgentState) -> AgentState:
    intel = gather_intel(state["alert"], db=state.get("db"))
    enriched = enrich_alert(state["alert"], intel)
    state["alert"] = enriched
    state["evidence"] = intel
    _step(state, "investigate", "completed", {"technique": intel.get("technique_id"), "docs": len(intel.get("documents") or [])})
    return state


async def analyze_node(state: AgentState) -> AgentState:
    analysis = await analyze(state["alert"], state.get("evidence") or {})
    analysis["correlation"] = correlate([state["alert"]])
    state["analysis"] = analysis
    _step(state, "analyze", "completed", analysis)
    return state


def decide_node(state: AgentState) -> AgentState:
    decision = decide_response(state["alert"], state.get("analysis") or {})
    state["decision"] = decision
    _step(state, "decide", "completed", decision)
    return state


def execute_node(state: AgentState) -> AgentState:
    decision = state.get("decision") or {"type": "MONITOR"}
    guardrail = validate_action(decision, agent_id="response")
    state["guardrail"] = guardrail
    if not guardrail["allowed"] or decision.get("requires_approval"):
        execution = {
            "status": "pending_human",
            "reason": guardrail.get("reasons") or ["human_approval_required"],
            "simulated": True,
        }
    else:
        execution = {
            "status": "simulated_ok",
            "action": decision.get("primary_action"),
            "target": decision.get("target"),
            "note": "No destructive connector enabled in this deployment; action is recorded, not executed on infra.",
        }
    state["execution"] = execution
    _step(state, "execute", execution["status"], execution)
    return state


def report_node(state: AgentState) -> AgentState:
    incident = {
        "title": f"{state['alert'].get('type')} from {state['alert'].get('src_ip')}",
        "severity": (state.get("analysis") or {}).get("severity") or state["alert"].get("severity"),
        "status": "investigating",
        "alerts": [state["alert"]],
        "analysis": state.get("analysis"),
        "decision": state.get("decision"),
        "guardrail": state.get("guardrail"),
        "created_at": state["alert"].get("timestamp"),
    }
    report = generate_report(incident)
    state["report"] = report
    _step(state, "report", "completed", {"sections": report["sections"]})
    return state


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify_node)
    graph.add_node("investigate", investigate_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("decide", decide_node)
    graph.add_node("execute", execute_node)
    graph.add_node("report", report_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "investigate")
    graph.add_edge("investigate", "analyze")
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "execute")
    graph.add_edge("execute", "report")
    graph.add_edge("report", END)
    return graph


_COMPILED = None


def compile_graph():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_graph().compile()
    return _COMPILED


async def invoke(alert: dict[str, Any], db: Any = None) -> AgentState:
    app = compile_graph()
    initial: AgentState = {"alert": alert, "steps": [], "db": db}
    result = await app.ainvoke(initial)
    logger.info("orchestrator.completed", steps=len(result.get("steps") or []))
    return result


async def stream(alert: dict[str, Any], db: Any = None) -> AsyncIterator[dict[str, Any]]:
    app = compile_graph()
    initial: AgentState = {"alert": alert, "steps": [], "db": db}
    async for event in app.astream(initial):
        for node, payload in event.items():
            yield {"step": node, "status": "completed", "output": payload.get("steps", payload)[-1] if isinstance(payload.get("steps"), list) and payload["steps"] else payload}
