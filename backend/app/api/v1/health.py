from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health/live")
def health_live():
    """Liveness probe: verifies the process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
def health_ready():
    """Readiness probe: verifies service dependencies are initialized."""
    return {"status": "ready", "storage": "in-memory-demo"}
