from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.schemas.alert import AlertAcknowledgeRequest, AlertsListResponse, CashAlertDTO
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("", response_model=AlertsListResponse)
def get_alerts(include_acknowledged: bool = Query(default=False)):
    """Get active derived cash shortage and safety buffer breach alerts."""
    return alert_service.get_alerts(include_acknowledged=include_acknowledged)


@router.patch("/{alert_id}")
def update_alert(alert_id: str, payload: AlertAcknowledgeRequest):
    """Acknowledge or un-acknowledge an alert."""
    alert_service.acknowledge_alert(alert_id, payload.acknowledged)
    return {"status": "ok", "alert_id": alert_id, "acknowledged": payload.acknowledged}
