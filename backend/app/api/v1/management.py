from typing import Literal, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from app.services.phase2_service import (list_plans, get_plan, create_plan, update_plan, record_installment_payment, cancel_plan, budget_views, create_budget, update_budget, reminders, acknowledge_reminder, report_summary, today)

router = APIRouter(prefix="/api/v1", tags=["Business Management"])

class InstallmentInput(BaseModel):
    due_date: str
    amount_paise: int = Field(gt=0)

class PlanInput(BaseModel):
    customer_id: str
    plan_type: Literal["full_payment", "installments"]
    planned_amount_paise: int = Field(gt=0)
    start_date: str
    notes: str = ""
    installments: list[InstallmentInput]

class PlanPatchInput(BaseModel):
    notes: Optional[str] = None
    cancel_reason: Optional[str] = None

class PaymentInput(BaseModel):
    payment_id: str = Field(min_length=8, max_length=100)
    amount_paise: int = Field(gt=0)
    payment_date: str
    payment_method: str = "cash"

class CancelInput(BaseModel): reason: str = Field(min_length=1, max_length=500)

class BudgetInput(BaseModel):
    category: str = Field(min_length=1, max_length=60)
    period_start: str
    period_end: str
    budget_amount_paise: int = Field(gt=0)
    period_type: str = "custom"
    thresholds: list[int] = [75, 90, 100]

class ReminderUpdate(BaseModel): status: Literal["read", "acknowledged"]

@router.get("/repayment-plans")
def get_plans(): return {"items": list_plans()}

@router.post("/repayment-plans", status_code=201)
def post_plan(payload: PlanInput): return create_plan(payload.model_dump())

@router.get("/repayment-plans/{plan_id}")
def get_plan_detail(plan_id: str): return get_plan(plan_id)

@router.patch("/repayment-plans/{plan_id}")
def patch_plan(plan_id: str, payload: PlanPatchInput): return update_plan(plan_id, payload.model_dump(exclude_unset=True))

@router.post("/repayment-plans/{plan_id}/installments/{installment_id}/payments")
def post_payment(plan_id: str, installment_id: str, payload: PaymentInput): return record_installment_payment(plan_id, installment_id, payload.model_dump())

@router.patch("/repayment-plans/{plan_id}/cancel")
def patch_cancel(plan_id: str, payload: CancelInput): return cancel_plan(plan_id, payload.reason)

@router.get("/budgets")
def get_budgets(): return {"items": budget_views(), "basis": "Recorded paid expense transactions only."}

@router.post("/budgets", status_code=201)
def post_budget(payload: BudgetInput): return create_budget(payload.model_dump())

@router.patch("/budgets/{budget_id}")
def patch_budget(budget_id: str, payload: BudgetInput): return update_budget(budget_id, payload.model_dump())

@router.get("/reports/summary")
def get_report(start_date: str = Query(...), end_date: str = Query(...)): return report_summary(start_date, end_date)

@router.get("/reports/expenses")
def get_expenses_report(start_date: str = Query(...), end_date: str = Query(...)):
    rep = report_summary(start_date, end_date)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "items": rep["expenses_by_category"],
        "total_amount_paise": sum(x["amount_paise"] for x in rep["expenses_by_category"]),
    }

@router.get("/reports/receivables")
def get_receivables_report():
    t = today().isoformat()
    rep = report_summary(t, t)
    return {
        "items": rep["receivables"],
        "total_receivables_paise": sum(x["outstanding_paise"] for x in rep["receivables"]),
    }

@router.get("/reports/payables")
def get_payables_report():
    t = today().isoformat()
    rep = report_summary(t, t)
    return {
        "items": rep["payables"],
        "total_payables_paise": sum(x["amount_paise"] for x in rep["payables"]),
    }

@router.get("/reminders")
def get_reminders(): return {"items": reminders(), "external_delivery": False}

@router.patch("/reminders/{reminder_id}")
def patch_reminder(reminder_id: str, payload: ReminderUpdate): return acknowledge_reminder(reminder_id, payload.status)

