"""Store and tenant settings management."""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1/settings", tags=["Store Settings"])


class SettingsResponse(BaseModel):
    store_name: str
    currency: str = "INR"
    timezone: str = "Asia/Kolkata"
    opening_cash_paise: int
    cash_safety_buffer_paise: int


class SettingsUpdate(BaseModel):
    store_name: Optional[str] = Field(None, min_length=1, max_length=100)
    cash_safety_buffer_paise: Optional[int] = Field(None, ge=0)


@router.get("", response_model=SettingsResponse)
def get_settings():
    """Retrieve active business settings and safety buffer."""
    biz = seed_service.get_business()
    return SettingsResponse(
        store_name=biz.get("name") or "Demo Kirana Store",
        currency=biz.get("currency", "INR"),
        timezone=biz.get("timezone", "Asia/Kolkata"),
        opening_cash_paise=biz.get("opening_cash_paise", 1500000),
        cash_safety_buffer_paise=biz.get("cash_safety_buffer_paise", 1500000),
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate):
    """Update store configuration and cash safety buffer threshold."""
    updates = {}
    if payload.store_name is not None:
        updates["name"] = payload.store_name.strip()
    if payload.cash_safety_buffer_paise is not None:
        updates["cash_safety_buffer_paise"] = payload.cash_safety_buffer_paise

    if updates:
        seed_service.update_business(updates)

    biz = seed_service.get_business()
    return SettingsResponse(
        store_name=biz.get("name") or "Demo Kirana Store",
        currency=biz.get("currency", "INR"),
        timezone=biz.get("timezone", "Asia/Kolkata"),
        opening_cash_paise=biz.get("opening_cash_paise", 1500000),
        cash_safety_buffer_paise=biz.get("cash_safety_buffer_paise", 1500000),
    )
