from app.api.v1.alerts import router as alerts_router
from app.api.v1.metrics import router as metrics_router
from app.api.v1.graph import router as graph_router
from app.api.v1.insights import router as insights_router

__all__ = ["alerts_router", "metrics_router", "graph_router", "insights_router"]
