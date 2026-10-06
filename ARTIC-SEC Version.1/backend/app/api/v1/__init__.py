from fastapi import APIRouter

from app.api.v1 import agents, alerts, graph, incidents, insights, metrics

api_router = APIRouter()
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(graph.router, prefix="/attack-graph", tags=["graph"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(insights.router, prefix="/ai-insights", tags=["insights"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
