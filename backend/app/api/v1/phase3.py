from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas.ai import (DraftReminderRequest, ExplainForecastRequest, ImportPreviewRequest, NotificationPreferencesPatch, SummarizeBusinessRequest)
from app.services.ai.service import explain
from app.services.phase3_service import (confirm_import, draft_reminder, explain_alert, explain_forecast, export_csv, expense_import_template, get_import_batch, notification_preferences, preview_expense_import, summarize_business, update_notification_preferences)

router=APIRouter(prefix="/api/v1",tags=["AI and Automation"])
_ai_requests=defaultdict(deque)

def _request_id(request: Request) -> str:
    return getattr(request.state,"request_id","req_unknown")

def _limit_ai(request: Request) -> None:
    now=datetime.now(timezone.utc); host=request.client.host if request.client else "unknown"; queue=_ai_requests[host]
    while queue and (now-queue[0])>timedelta(minutes=1): queue.popleft()
    if len(queue)>=10: raise HTTPException(429,"AI request limit reached. Try again in a minute.")
    queue.append(now)

@router.post("/ai/explain-forecast")
def explain_forecast_route(payload: ExplainForecastRequest,request: Request):
    _limit_ai(request); return explain_forecast(payload.horizon_days,_request_id(request))

@router.post("/ai/explain-alert/{alert_id}")
def explain_alert_route(alert_id: str,request: Request):
    _limit_ai(request); return explain_alert(alert_id,_request_id(request))

@router.post("/ai/summarize-business")
def summarize_business_route(payload: SummarizeBusinessRequest,request: Request):
    _limit_ai(request); return summarize_business(payload.period_days,_request_id(request))

@router.post("/ai/draft-reminder")
def draft_reminder_route(payload: DraftReminderRequest,request: Request):
    _limit_ai(request); return draft_reminder(payload.customer_id,payload.installment_id,payload.context,_request_id(request))

@router.get("/exports/{export_type}")
def export_route(export_type: str,from_date: str|None=None,to_date: str|None=None):
    name,data=export_csv(export_type,from_date,to_date)
    return StreamingResponse(BytesIO(data),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="{name}"',"X-Export-Schema-Version":"1"})

@router.post("/imports/preview")
def preview_import_route(payload: ImportPreviewRequest): return preview_expense_import(payload.file_name,payload.csv_text)

@router.get("/imports/templates/expenses")
def expense_template_route():
    return StreamingResponse(BytesIO(expense_import_template()),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":'attachment; filename="dukaanflow-expense-import-template-v1.csv"'})

@router.get("/imports/{batch_id}")
def get_import_route(batch_id: str): return get_import_batch(batch_id)

@router.post("/imports/{batch_id}/confirm")
def confirm_import_route(batch_id: str): return confirm_import(batch_id)

@router.post("/imports/{batch_id}/cancel")
def cancel_import_route(batch_id: str):
    from app.services.seed_data import seed_service
    batch=seed_service._data.setdefault("import_batches",{}).get(batch_id)
    if not batch: raise HTTPException(404,"Import batch not found")
    if batch["status"]=="completed": raise HTTPException(409,"A completed import cannot be cancelled")
    batch["status"]="cancelled"; batch["rows"]=[]
    return get_import_batch(batch_id)

@router.get("/notification-preferences")
def get_notification_preferences(): return notification_preferences()

@router.patch("/notification-preferences")
def patch_notification_preferences(payload: NotificationPreferencesPatch): return update_notification_preferences(payload.model_dump())
