from fastapi import APIRouter
from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1/seed", tags=["Seed Data"])


@router.post("/reset")
def reset_seed():
    """Reset the demo business and ledger data back to canonical seed defaults."""
    return seed_service.reset()
