from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def health_live():
    """Liveness probe: verifies the process is running."""
    return {"status": "alive"}


from app.core.database import get_db

@router.get("/health/ready")
def health_ready():
    """Readiness probe: verifies service dependencies are initialized."""
    db_health = get_db().check_health()
    return {
        "status": "ready" if db_health.get("connected") else "degraded",
        "storage": db_health.get("mode", "in_memory"),
        "database": db_health,
    }
