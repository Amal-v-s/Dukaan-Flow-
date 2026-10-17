"""In-memory Phase 2 management features for the demo business."""
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.services.seed_data import seed_service
from app.domain.ledger import calculate_customer_balance, validate_repayment_amount
from app.core.config import settings


def today() -> date:
    return datetime.now(ZoneInfo(settings.DEFAULT_TIMEZONE)).date()


def _store() -> dict[str, Any]:
    return seed_service._data


def plans() -> list[dict]:
    return _store().setdefault("repayment_plans", [])


def plan_view(plan: dict) -> dict:
    now = today()
    for inst in plan["installments"]:
        rem = inst["amount_paise"] - inst["paid_amount_paise"]
        due_d = date.fromisoformat(inst["due_date"])
        inst["days_overdue"] = max(0, (now - due_d).days) if (due_d < now and rem > 0) else 0
        inst["status"] = "paid" if rem == 0 else ("overdue" if due_d < now else ("partially_paid" if inst["paid_amount_paise"] else "upcoming"))
    paid = sum(x["paid_amount_paise"] for x in plan["installments"])
    remaining = plan["planned_amount_paise"] - paid
    plan["paid_amount_paise"] = paid
    plan["remaining_amount_paise"] = remaining
    plan["days_overdue"] = max([inst["days_overdue"] for inst in plan["installments"]] or [0])
    if plan.get("status") != "cancelled":
        plan["status"] = "completed" if remaining == 0 else ("overdue" if any(x["status"] == "overdue" for x in plan["installments"]) else "active")
    return plan


def list_plans() -> list[dict]:
    return [plan_view(p) for p in plans()]


def get_plan(plan_id: str) -> dict:
    p = next((item for item in plans() if item["id"] == plan_id), None)
    if not p: raise HTTPException(404, "Repayment plan not found")
    return plan_view(p)


def allocate_unplanned_repayment(customer_id: str, amount_paise: int, payment_date: str) -> None:
    """Apply ordinary khata repayments to scheduled debt FIFO by due date."""
    remaining = amount_paise
    customer_plans = sorted((p for p in plans() if p["customer_id"] == customer_id and p.get("status") != "cancelled"), key=lambda p: p["final_due_date"])
    for plan in customer_plans:
        for installment in sorted(plan["installments"], key=lambda i: (i["due_date"], i["sequence_number"])):
            outstanding = installment["amount_paise"] - installment["paid_amount_paise"]
            applied = min(remaining, outstanding)
            if applied:
                installment["paid_amount_paise"] += applied
                installment.setdefault("payments", []).append({"id": f"external_{uuid4().hex[:10]}", "amount_paise": applied, "payment_date": payment_date, "source": "khata_repayment"})
                remaining -= applied
            if remaining == 0: break
        if remaining == 0: break


def create_plan(payload: dict) -> dict:
    customer = next((c for c in seed_service.get_customers() if c["id"] == payload["customer_id"]), None)
    if not customer:
        raise HTTPException(404, "Customer not found")
    balance, _, _ = calculate_customer_balance(customer.get("credit_entries", []))
    amount = payload["planned_amount_paise"]
    already_allocated = sum(p["planned_amount_paise"] - p.get("paid_amount_paise", 0) for p in plans() if p["customer_id"] == customer["id"] and p["status"] not in ("cancelled",))
    if amount <= 0 or amount > balance - already_allocated:
        raise HTTPException(400, "Plan amount must fit the unallocated customer balance")
    installments = payload["installments"]
    if not installments or sum(x["amount_paise"] for x in installments) != amount:
        raise HTTPException(400, "Instalment amounts must sum exactly to planned amount")
    if payload["plan_type"] == "full_payment" and len(installments) != 1:
        raise HTTPException(400, "A full-payment plan must contain exactly one instalment")
    if payload["plan_type"] == "installments" and len(installments) < 2:
        raise HTTPException(400, "An instalment plan must contain at least two instalments")
    dates = [date.fromisoformat(x["due_date"]) for x in installments]
    if dates != sorted(dates) or date.fromisoformat(payload["start_date"]) > dates[0]:
        raise HTTPException(400, "Plan dates must be in ascending order from the start date")
    already_linked = {}
    for plan in plans():
        if plan["customer_id"] == customer["id"] and plan["status"] != "cancelled":
            for entry_id, allocated in plan.get("source_allocations_paise", {}).items():
                already_linked[entry_id] = already_linked.get(entry_id, 0) + allocated
    eligible_entries = [e for e in customer.get("credit_entries", []) if e.get("entry_type") == "credit_sale" and e.get("status", "posted") == "posted" and e["amount_paise"] > already_linked.get(e["id"], 0)]
    # Link only enough unallocated credit-sale records to cover this schedule.
    source_ids = []
    source_allocations = {}
    linked_total = 0
    for entry in eligible_entries:
        allocation = min(amount - linked_total, entry["amount_paise"] - already_linked.get(entry["id"], 0))
        source_ids.append(entry["id"]); source_allocations[entry["id"]] = allocation; linked_total += allocation
        if linked_total >= amount: break
    if linked_total < amount:
        raise HTTPException(400, "There are not enough unallocated credit-sale records for this plan")
    p = {"id": f"plan_{uuid4().hex[:10]}", "customer_id": customer["id"], "customer_name": customer["name"], "source_ledger_entry_ids": source_ids, "plan_type": payload["plan_type"], "planned_amount_paise": amount, "paid_amount_paise": 0, "remaining_amount_paise": amount, "start_date": payload["start_date"], "final_due_date": dates[-1].isoformat(), "status": "active", "notes": payload.get("notes", ""), "installments": [{"id": f"inst_{uuid4().hex[:10]}", "sequence_number": i+1, "due_date": date.fromisoformat(x["due_date"]).isoformat(), "amount_paise": x["amount_paise"], "paid_amount_paise": 0, "status": "upcoming", "payments": []} for i, x in enumerate(installments)], "created_at": datetime.now().isoformat()}
    p["source_allocations_paise"] = source_allocations
    plans().append(p)
    return plan_view(p)


def record_installment_payment(plan_id: str, installment_id: str, payload: dict) -> dict:
    p = next((x for x in plans() if x["id"] == plan_id), None)
    if not p: raise HTTPException(404, "Repayment plan not found")
    inst = next((x for x in p["installments"] if x["id"] == installment_id), None)
    if not inst: raise HTTPException(404, "Instalment not found")
    if p["status"] in ("completed", "cancelled"): raise HTTPException(409, "This plan cannot accept payments")
    amount = payload["amount_paise"]
    prior_payment = next((payment for installment in p["installments"] for payment in installment.get("payments", []) if payment["id"] == payload["payment_id"]), None)
    if prior_payment:
        if prior_payment["amount_paise"] != amount or prior_payment["payment_date"] != payload["payment_date"]:
            raise HTTPException(409, "Payment id was already used with different payment details")
        return plan_view(p)
    remaining_inst = inst["amount_paise"] - inst["paid_amount_paise"]
    if amount <= 0 or amount > remaining_inst: raise HTTPException(400, "Payment must be positive and cannot exceed this instalment's remaining amount")
    # Validate against actual ledger, then apply exactly one ledger entry and cash movement.
    customer = next(c for c in seed_service.get_customers() if c["id"] == p["customer_id"])
    balance, _, _ = calculate_customer_balance(customer.get("credit_entries", []))
    try: validate_repayment_amount(balance, amount)
    except ValueError as exc: raise HTTPException(400, str(exc))
    payment_id = payload["payment_id"]
    payment_date = payload["payment_date"]
    inst["paid_amount_paise"] += amount
    inst["payments"].append({"id": payment_id, "amount_paise": amount, "payment_date": payment_date})
    ledger_id = f"entry_{uuid4().hex[:8]}"
    customer.setdefault("credit_entries", []).append({"id": ledger_id, "entry_type": "repayment", "amount_paise": amount, "effective_date": payment_date, "status": "posted", "payment_method": payload.get("payment_method", "cash"), "notes": f"Repayment plan {p['id']}", "created_at": datetime.now().isoformat()})
    seed_service.get_transactions().append({"id": f"tx_{payment_id}", "type": "repayment", "description": f"{customer['name']} plan instalment payment", "amount_paise": amount, "date": payment_date, "direction": "inflow", "payment_method": payload.get("payment_method", "cash")})
    seed_service.get_business()["opening_cash_paise"] += amount
    _store().setdefault("audit_events", []).append({"id": f"audit_{uuid4().hex[:8]}", "type": "repayment_plan_payment", "source_id": payment_id, "created_at": datetime.now().isoformat()})
    return plan_view(p)


def cancel_plan(plan_id: str, reason: str) -> dict:
    p = next((x for x in plans() if x["id"] == plan_id), None)
    if not p: raise HTTPException(404, "Repayment plan not found")
    if p["paid_amount_paise"]: raise HTTPException(409, "Plans with payments cannot be cancelled in the demo")
    if not reason.strip(): raise HTTPException(400, "Cancellation reason is required")
    p["status"] = "cancelled"; p["cancel_reason"] = reason.strip()
    _store().setdefault("audit_events", []).append({"id": f"audit_{uuid4().hex[:8]}", "type": "repayment_plan_cancelled", "source_id": plan_id, "reason": reason.strip(), "created_at": datetime.now().isoformat()})
    return plan_view(p)


def update_plan(plan_id: str, payload: dict) -> dict:
    p = next((x for x in plans() if x["id"] == plan_id), None)
    if not p: raise HTTPException(404, "Repayment plan not found")
    if "notes" in payload and payload["notes"] is not None:
        p["notes"] = payload["notes"]
    if "cancel_reason" in payload and payload["cancel_reason"]:
        return cancel_plan(plan_id, payload["cancel_reason"])
    return plan_view(p)



def budgets() -> list[dict]: return _store().setdefault("budgets", [])

def budget_views() -> list[dict]:
    txs = seed_service.get_transactions(); result=[]
    for b in budgets():
        spent=sum(t["amount_paise"] for t in txs if t.get("type")=="expense" and t.get("category")==b["category"] and b["period_start"] <= t["date"] <= b["period_end"])
        pct=(spent*100)//b["budget_amount_paise"]
        thresholds=[x for x in b["thresholds"] if pct >= x]
        result.append({**b,"spent_paise":spent,"remaining_paise":b["budget_amount_paise"]-spent,"utilization_percent":pct,"triggered_thresholds":thresholds,"exceeded":spent>b["budget_amount_paise"]})
    return result


def create_budget(payload: dict) -> dict:
    if date.fromisoformat(payload["period_end"]) < date.fromisoformat(payload["period_start"]): raise HTTPException(400,"Budget period end must be on or after start")
    if any(b["category"]==payload["category"] and b["period_start"]==payload["period_start"] and b["period_end"]==payload["period_end"] for b in budgets()): raise HTTPException(409,"A budget already exists for this category and period")
    b={"id":f"budget_{uuid4().hex[:10]}","category":payload["category"],"period_type":payload.get("period_type","custom"),"period_start":payload["period_start"],"period_end":payload["period_end"],"budget_amount_paise":payload["budget_amount_paise"],"thresholds":payload.get("thresholds",[75,90,100]),"created_at":datetime.now().isoformat()}
    budgets().append(b); return next(x for x in budget_views() if x["id"]==b["id"])


def update_budget(budget_id: str, payload: dict) -> dict:
    b=next((x for x in budgets() if x["id"]==budget_id),None)
    if not b: raise HTTPException(404,"Budget not found")
    for key in ("category","period_start","period_end","budget_amount_paise","thresholds"):
        if key in payload and payload[key] is not None: b[key]=payload[key]
    if date.fromisoformat(b["period_end"]) < date.fromisoformat(b["period_start"]): raise HTTPException(400,"Budget period end must be on or after start")
    return next(x for x in budget_views() if x["id"]==budget_id)


def reminders() -> list[dict]:
    store=_store().setdefault("reminders",{}); now=today(); due=[]
    for p in list_plans():
        for i in p["installments"]:
            rem=i["amount_paise"]-i["paid_amount_paise"]
            if rem and date.fromisoformat(i["due_date"]) <= now+timedelta(days=7): due.append(("customer_instalment",i["id"],p["customer_name"],i["due_date"],rem,p["id"]))
    for bill in seed_service.get_supplier_bills():
        if bill["remaining_amount_paise"] and date.fromisoformat(bill["due_date"]) <= now+timedelta(days=7): due.append(("supplier_bill",bill["id"],bill["supplier_name"],bill["due_date"],bill["remaining_amount_paise"],bill["id"]))
    for typ,src,title,due_date,amount,parent in due:
        key=f"{typ}:{src}:{due_date}"
        store.setdefault(key,{"id":f"rem_{uuid4().hex[:10]}","type":typ,"source_id":src,"parent_id":parent,"title":title,"due_date":due_date,"amount_paise":amount,"status":"unread"})
        store[key]["amount_paise"]=amount
        store[key]["due_state"]="overdue" if date.fromisoformat(due_date) < now else ("due_today" if date.fromisoformat(due_date) == now else "upcoming")
    active_keys={f"{typ}:{src}:{due_date}" for typ,src,title,due_date,amount,parent in due}
    return sorted((store[key] for key in active_keys), key=lambda x:x["due_date"])


def acknowledge_reminder(reminder_id: str, status: str) -> dict:
    r=next((x for x in reminders() if x["id"]==reminder_id),None)
    if not r: raise HTTPException(404,"Reminder not found")
    r["status"]=status; return r


def report_summary(start: str, end: str) -> dict:
    start_d=date.fromisoformat(start); end_d=date.fromisoformat(end)
    if end_d < start_d: raise HTTPException(400,"End date must be on or after start date")
    txs=[t for t in seed_service.get_transactions() if start<=t["date"]<=end]
    expenses={}
    for t in txs:
        if t["type"]=="expense": expenses[t.get("category","misc")]=expenses.get(t.get("category","misc"),0)+t["amount_paise"]
    cust=[]
    for c in seed_service.get_customers():
        bal,_,_=calculate_customer_balance(c.get("credit_entries",[]))
        cust.append({"customer_id":c["id"],"name":c["name"],"outstanding_paise":bal})
    return {"start_date":start,"end_date":end,"generated_at":datetime.now().isoformat(),"cash_inflows_paise":sum(t["amount_paise"] for t in txs if t["direction"]=="inflow"),"cash_outflows_paise":sum(t["amount_paise"] for t in txs if t["direction"]=="outflow"),"expenses_by_category":[{"category":k,"amount_paise":v} for k,v in sorted(expenses.items())],"receivables":cust,"payables":[{"bill_id":b["id"],"supplier_name":b["supplier_name"],"amount_paise":b["remaining_amount_paise"],"due_date":b["due_date"]} for b in seed_service.get_supplier_bills() if b["remaining_amount_paise"]],"repayment_plans":list_plans(),"budgets":budget_views()}
