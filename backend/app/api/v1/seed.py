from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.services.seed_data import seed_service
from app.core.tenant_context import get_business_id

router = APIRouter(prefix="/api/v1/seed", tags=["Seed Data"])


@router.post("/reset")
def reset_seed():
    """Reset the demo business and ledger data back to canonical seed defaults.
    
    Guarded behind ENVIRONMENT=development to prevent data loss in non-dev environments.
    """
    if settings.ENVIRONMENT.lower() not in {"development", "test", "testing", "dev"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed data reset is only allowed in development environments.",
        )
    if get_business_id() != "biz_demo_kirana":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the demo tenant can be reset.")
    return seed_service.reset()
