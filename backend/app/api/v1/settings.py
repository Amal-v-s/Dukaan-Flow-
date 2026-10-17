"""Business settings API."""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


class SafetyBufferUpdate(BaseModel):
    cash_safety_buffer_paise: int = Field(ge=0, le=100_000_000_000)


@router.get("")
def get_settings():
    business = seed_service.get_business()
    return {
        "cash_safety_buffer_paise": business.get("cash_safety_buffer_paise", 1_500_000),
        "business_name": business.get("name", ""),
        "currency": business.get("currency", "INR"),
        "timezone": business.get("timezone", "Asia/Kolkata"),
    }


@router.patch("/safety-buffer")
def update_safety_buffer(payload: SafetyBufferUpdate):
    business = seed_service.get_business()
    business["cash_safety_buffer_paise"] = payload.cash_safety_buffer_paise
    return {"cash_safety_buffer_paise": payload.cash_safety_buffer_paise}
