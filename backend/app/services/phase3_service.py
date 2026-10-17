"""Server-calculated facts, CSV workflows, and notification preferences."""
import csv
import hashlib
import io
import re
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException
from app.core.config import settings
from app.domain.ledger import calculate_customer_balance
from app.schemas.ai import GroundedExplanation, ReminderDraftResponse
from app.schemas.supplier import ExpenseCreateRequest
from app.services.ai.service import explain
from app.services.phase2_service import budget_views, list_plans, report_summary, today
from app.services.seed_data import seed_service
from app.services.supplier_service import supplier_service


def _all_source_ids() -> set[str]:
    ids=set()
    for customer in seed_service.get_customers():
        ids.add(customer["id"]); ids.update(e["id"] for e in customer.get("credit_entries", []))
    for bill in seed_service.get_supplier_bills(): ids.add(bill["id"])
    ids.update(b["id"] for b in budget_views())
    for plan in list_plans():
        ids.add(plan["id"]); ids.update(i["id"] for i in plan["installments"])
    return ids


def explain_forecast(horizon_days: int, request_id: str) -> dict:
    from app.api.v1.cashflow import get_forecast
    forecast=get_forecast(horizon_days)
    contributors=[c for d in forecast.days for c in d.contributors]
    source_ids=list(dict.fromkeys(c.source_id for c in contributors))[:20]
    breach=forecast.shortage_detected or forecast.buffer_breached
    facts={"use_case":"cash_flow_forecast","as_of_date":today().isoformat(),"business_timezone":settings.DEFAULT_TIMEZONE,"forecast_horizon_days":forecast.horizon_days,"lowest_balance_paise":forecast.lowest_dip_paise,"lowest_balance_date":forecast.lowest_dip_date,"safety_buffer_paise":forecast.cash_safety_buffer_paise,"shortage_detected":forecast.shortage_detected,"buffer_breached":forecast.buffer_breached,"assumptions":forecast.assumptions,"contributors":[{"source_id":c.source_id,"source_type":c.source_type,"amount_paise":c.amount_paise} for c in contributors[:40]],"source_ids":source_ids,"fallback_summary":"The recorded forecast indicates a cash-flow risk. Review the scheduled movements and assumptions shown with the forecast.","fallback_reasons":["The explanation is based on the deterministic forecast and its listed contributors."],"fallback_actions":[{"label":"Review the forecast","type":"cash_flow","target_id":None}],"disclaimer":"Forecast collections are estimates and are not guaranteed." if breach else "This explanation uses recorded data and deterministic projections."}
    return explain("forecast",facts,request_id)


def explain_alert(alert_id: str, request_id: str) -> dict:
    from app.services.alert_service import alert_service
    found=next((a for a in alert_service.get_alerts(include_acknowledged=True).alerts if a.id==alert_id),None)
    if not found: raise HTTPException(404,"Alert not found")
    ids=[c.source_id for c in found.contributing_events]
    valid=_all_source_ids()
    if any(x not in valid for x in ids): raise HTTPException(404,"Alert source record not found")
    facts={"use_case":"cash_shortage_alert","severity":found.severity,"breach_date":found.breach_date,"projected_balance_paise":found.projected_balance_paise,"threshold_paise":found.threshold_paise,"contributing_events":[{"source_id":c.source_id,"source_type":c.source_type,"amount_paise":c.amount_paise,"direction":c.direction} for c in found.contributing_events],"source_ids":ids,"fallback_summary":"A recorded cash-flow alert was triggered. Review the listed scheduled movements against the deterministic forecast.","fallback_reasons":["The alert is derived from projected closing cash and the configured safety threshold."],"fallback_actions":[{"label":"Review the forecast","type":"cash_flow","target_id":None}],"disclaimer":"Forecasts depend on recorded data and estimated collection dates."}
    return explain("alert",facts,request_id)


def summarize_business(period_days: int, request_id: str) -> dict:
    end=today(); start=end-timedelta(days=period_days-1)
    report=report_summary(start.isoformat(),end.isoformat())
    plan_list=list_plans(); overdue=[p for p in plan_list if p["status"]=="overdue"]
    budgets=budget_views(); flagged=[b for b in budgets if b["triggered_thresholds"]]
    from app.api.v1.cashflow import get_forecast
    forecast=get_forecast(14)
    risk_days=[{"date":d.date,"closing_balance_paise":d.closing_balance_paise,"below_zero":d.below_zero,"below_safety_buffer":d.below_safety_buffer} for d in forecast.days if d.below_zero or d.below_safety_buffer]
    source_ids=[x["customer_id"] for x in report["receivables"]]+[x["bill_id"] for x in report["payables"]]+[p["id"] for p in overdue]+[b["id"] for b in flagged]+[c.source_id for d in forecast.days for c in d.contributors]
    unique_ids=list(dict.fromkeys(source_ids))[:20]
    if flagged: action={"label":"Review budget utilization","type":"budget","target_id":flagged[0]["id"]}
    elif report["payables"]: action={"label":"Review supplier bills","type":"supplier_bill","target_id":report["payables"][0]["bill_id"]}
    elif overdue: action={"label":"Review customer repayment plan","type":"customer","target_id":overdue[0]["customer_id"]}
    else: action={"label":"Review cash flow","type":"cash_flow","target_id":None}
    facts={"use_case":"business_brief","period_start":start.isoformat(),"period_end":end.isoformat(),"cash_inflows_paise":report["cash_inflows_paise"],"cash_outflows_paise":report["cash_outflows_paise"],"expense_categories":report["expenses_by_category"],"overdue_plan_count":len(overdue),"budget_alert_count":len(flagged),"payables_count":len(report["payables"]),"receivables_count":len(report["receivables"]),"forecast_horizon_days":forecast.horizon_days,"forecast_risk_days":risk_days,"source_ids":unique_ids,"fallback_summary":"The business brief summarizes recorded cash movements, outstanding items, budget status, and the deterministic forecast.","fallback_reasons":["Receivables and payables are shown separately from cash movement."],"fallback_actions":[action],"disclaimer":"This brief is based only on records entered in DukaanFlow. Forecast collections are estimates."}
    return explain("business_brief",facts,request_id)


def draft_reminder(customer_id: str, installment_id: str | None, context: str, request_id: str) -> dict:
    customer=next((c for c in seed_service.get_customers() if c["id"]==customer_id),None)
    if not customer: raise HTTPException(404,"Customer not found")
    balance,_,_=calculate_customer_balance(customer.get("credit_entries",[]))
    due_date=None; amount=balance; source_ids=[customer_id]
    if installment_id:
        found=None
        for plan in list_plans():
            for inst in plan["installments"]:
                if inst["id"]==installment_id and plan["customer_id"]==customer_id: found=(plan,inst); break
        if not found: raise HTTPException(404,"Instalment not found for this customer")
        plan,inst=found; due_date=inst["due_date"]; amount=inst["amount_paise"]-inst["paid_amount_paise"]; source_ids.append(installment_id)
    if amount<=0: raise HTTPException(400,"No outstanding amount is available for a reminder draft")
    safe_name=re.sub(r"[^\w .'-]","",customer["name"]).strip()[:80] or "Customer"
    template=f"Hello {safe_name}, this is a polite reminder about the outstanding payment{f' due on {due_date}' if due_date else ''}. Please contact us if you have already paid or would like to discuss it. Thank you."
    facts={"use_case":"reminder_draft","customer_display_name":safe_name,"remaining_amount_paise":amount,"due_date":due_date,"merchant_context":context,"source_ids":source_ids,"fallback_summary":template,"fallback_reasons":[],"fallback_actions":[],"disclaimer":"Draft only. Review and edit before using; no message has been sent."}
    result=explain("reminder_draft",facts,request_id)
    draft=result["summary"]
    return ReminderDraftResponse(mode="ai_draft" if result["mode"]=="ai_explanation" else "template_fallback",message=draft,requires_merchant_review=True,sent=False,due_date=due_date,remaining_amount_paise=amount).model_dump()


EXPORT_FIELDS={
    "customers":["schema_version","customer_id","name","outstanding_paise","total_credit_paise","total_repaid_paise"],
    "ledger":["schema_version","entry_id","customer_id","entry_type","amount_paise","effective_date","due_date","status"],
    "supplier-bills":["schema_version","bill_id","supplier_id","supplier_name","description","bill_amount_paise","paid_amount_paise","remaining_amount_paise","bill_date","due_date","status"],
    "supplier-payments":["schema_version","payment_id","bill_id","supplier_id","amount_paise","payment_date","payment_method"],
    "expenses":["schema_version","expense_id","title","category","amount_paise","expense_date","payment_method"],
    "repayment-plans":["schema_version","plan_id","customer_id","customer_name","plan_type","installment_id","due_date","amount_paise","paid_amount_paise","status"],
    "budgets":["schema_version","budget_id","category","period_start","period_end","budget_amount_paise","spent_paise","remaining_paise","utilization_percent"],
    "reports":["schema_version","section","name","amount_paise","period_start","period_end"],
}

def _safe_cell(value: Any) -> Any:
    if isinstance(value,str) and value.lstrip().startswith(("=","+","-","@")):
        return "'"+value
    return value

def export_csv(export_type: str, from_date: str | None=None, to_date: str | None=None) -> tuple[str, bytes]:
    if export_type not in EXPORT_FIELDS: raise HTTPException(400,"Unsupported export type")
    for value in (from_date,to_date):
        if value:
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",value): raise ValueError
                date.fromisoformat(value)
            except ValueError: raise HTTPException(400,"Dates must use YYYY-MM-DD")
    if from_date and to_date and from_date>to_date: raise HTTPException(400,"from_date must not be after to_date")
    rows=[]
    if export_type=="customers":
        for c in seed_service.get_customers():
            bal,credit,repaid=calculate_customer_balance(c.get("credit_entries",[])); rows.append({"customer_id":c["id"],"name":c["name"],"outstanding_paise":bal,"total_credit_paise":credit,"total_repaid_paise":repaid})
    elif export_type=="ledger":
        for c in seed_service.get_customers():
            for e in c.get("credit_entries",[]): rows.append({"entry_id":e["id"],"customer_id":c["id"],"entry_type":e["entry_type"],"amount_paise":e["amount_paise"],"effective_date":e["effective_date"],"due_date":e.get("due_date") or "","status":e.get("status","posted")})
    elif export_type=="supplier-bills": rows=[{"bill_id":b["id"],"supplier_id":b["supplier_id"],"supplier_name":b["supplier_name"],"description":b["description"],"bill_amount_paise":b["bill_amount_paise"],"paid_amount_paise":b["paid_amount_paise"],"remaining_amount_paise":b["remaining_amount_paise"],"bill_date":b["bill_date"],"due_date":b["due_date"],"status":b["status"]} for b in seed_service.get_supplier_bills()]
    elif export_type=="supplier-payments": rows=[{"payment_id":p["id"],"bill_id":b["id"],"supplier_id":b["supplier_id"],"amount_paise":p["amount_paise"],"payment_date":p["payment_date"],"payment_method":p["payment_method"]} for b in seed_service.get_supplier_bills() for p in b.get("payments",[])]
    elif export_type=="expenses": rows=[{"expense_id":t["id"],"title":t["description"],"category":t.get("category","misc"),"amount_paise":t["amount_paise"],"expense_date":t["date"],"payment_method":t.get("payment_method","cash")} for t in seed_service.get_transactions() if t.get("type")=="expense"]
    elif export_type=="repayment-plans":
        for p in list_plans():
            for i in p["installments"]: rows.append({"plan_id":p["id"],"customer_id":p["customer_id"],"customer_name":p["customer_name"],"plan_type":p["plan_type"],"installment_id":i["id"],"due_date":i["due_date"],"amount_paise":i["amount_paise"],"paid_amount_paise":i["paid_amount_paise"],"status":i["status"]})
    elif export_type=="budgets": rows=[{"budget_id":b["id"],"category":b["category"],"period_start":b["period_start"],"period_end":b["period_end"],"budget_amount_paise":b["budget_amount_paise"],"spent_paise":b["spent_paise"],"remaining_paise":b["remaining_paise"],"utilization_percent":b["utilization_percent"]} for b in budget_views()]
    elif export_type=="reports":
        if not from_date or not to_date: raise HTTPException(400,"Report export requires from_date and to_date")
        report=report_summary(from_date,to_date)
        rows=[{"section":"cash_movement","name":"cash_inflows","amount_paise":report["cash_inflows_paise"],"period_start":from_date,"period_end":to_date},{"section":"cash_movement","name":"cash_outflows","amount_paise":report["cash_outflows_paise"],"period_start":from_date,"period_end":to_date}]
        rows.extend({"section":"expense_category","name":item["category"],"amount_paise":item["amount_paise"],"period_start":from_date,"period_end":to_date} for item in report["expenses_by_category"])
        rows.extend({"section":"receivable","name":item["name"],"amount_paise":item["outstanding_paise"],"period_start":from_date,"period_end":to_date} for item in report["receivables"])
        rows.extend({"section":"payable","name":item["supplier_name"],"amount_paise":item["amount_paise"],"period_start":from_date,"period_end":to_date} for item in report["payables"])
    date_col={"ledger":"effective_date","supplier-bills":"bill_date","supplier-payments":"payment_date","expenses":"expense_date","repayment-plans":"due_date"}.get(export_type)
    if date_col: rows=[r for r in rows if (not from_date or r.get(date_col,"")>=from_date) and (not to_date or r.get(date_col,"")<=to_date)]
    if not rows: raise HTTPException(404,"No records match the export filters")
    if len(rows)>10_000: raise HTTPException(413,"Export exceeds the 10,000 row limit")
    output=io.StringIO(newline=""); writer=csv.DictWriter(output,fieldnames=EXPORT_FIELDS[export_type],extrasaction="ignore",lineterminator="\r\n"); writer.writeheader()
    for row in rows: writer.writerow({"schema_version":"1",**{k:_safe_cell(v) for k,v in row.items()}})
    return f"dukaanflow-{export_type}-v1.csv",output.getvalue().encode("utf-8-sig")


def expense_import_template() -> bytes:
    return b"title,category,amount_inr,expense_date,payment_method,notes\r\nElectricity,utilities,1250.00,2026-10-17,cash,Monthly electricity bill\r\n"


ALLOWED_EXPENSE_CATEGORIES={"utilities","rent","transport","packaging","repairs","misc"}
IMPORT_COLUMNS={"title","category","amount_inr","expense_date","payment_method","notes"}

def preview_expense_import(file_name: str, csv_text: str) -> dict:
    if len(csv_text.encode("utf-8"))>1_000_000: raise HTTPException(413,"CSV is larger than 1 MB")
    if "\x00" in csv_text: raise HTTPException(400,"CSV contains invalid null characters")
    if "\ufffd" in csv_text: raise HTTPException(400,"CSV contains invalid text encoding; save the file as UTF-8 and retry")
    csv_text=csv_text.lstrip("\ufeff")
    try: reader=csv.DictReader(io.StringIO(csv_text, newline=""))
    except csv.Error: raise HTTPException(400,"CSV could not be parsed")
    headers=reader.fieldnames or []
    if len(headers)!=len(set(headers)): raise HTTPException(400,"CSV column names must be unique")
    missing={"title","category","amount_inr","expense_date"}-set(headers)
    if missing: raise HTTPException(400,f"Missing required columns: {', '.join(sorted(missing))}")
    if set(headers)-IMPORT_COLUMNS: raise HTTPException(400,"CSV contains unsupported columns")
    seen=set(); existing={(t.get("description"),t.get("category"),t.get("amount_paise"),t.get("date")) for t in seed_service.get_transactions() if t.get("type")=="expense"}
    rows=[]
    for row_num,row in enumerate(reader,start=2):
        # Leave headroom under Firestore's 500-write batch cap for the batch,
        # audit event, and business cash balance update.
        if row_num>401: raise HTTPException(413,"Import is limited to 400 rows")
        errors=[]
        if None in row: errors.append("row has more values than the header")
        title=(row.get("title") or "").strip(); category=(row.get("category") or "").strip().lower(); amount_text=(row.get("amount_inr") or "").strip(); expense_date=(row.get("expense_date") or "").strip(); method=(row.get("payment_method") or "cash").strip().lower(); notes=(row.get("notes") or "").strip()
        if not title or len(title)>100: errors.append("title is required and must be at most 100 characters")
        if len(notes)>500: errors.append("notes must be at most 500 characters")
        if category not in ALLOWED_EXPENSE_CATEGORIES: errors.append("category must be one of: utilities, rent, transport, packaging, repairs, misc")
        paise_int=0
        try:
            if not re.fullmatch(r"\d+(?:\.\d{1,2})?",amount_text): raise InvalidOperation
            amount=Decimal(amount_text)
            paise=amount*100
            if not amount.is_finite() or paise!=paise.to_integral_value() or paise<=0: errors.append("amount_inr must be positive with at most two decimal places")
            else: paise_int=int(paise)
        except (InvalidOperation,ValueError): errors.append("amount_inr must be a valid decimal rupee amount"); paise_int=0
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",expense_date): raise ValueError
            date.fromisoformat(expense_date)
        except ValueError: errors.append("expense_date must use YYYY-MM-DD")
        if method not in {"cash","upi","bank_transfer"}: errors.append("payment_method must be cash, upi, or bank_transfer")
        fingerprint=hashlib.sha256(f"{title}|{category}|{paise_int}|{expense_date}|{method}".encode()).hexdigest()
        if fingerprint in seen or (title,category,paise_int,expense_date) in existing: errors.append("possible duplicate expense")
        seen.add(fingerprint)
        rows.append({"row_number":row_num,"valid":not errors,"errors":errors,"normalized":{"title":title,"category":category,"amount_paise":paise_int,"expense_date":expense_date,"payment_method":method,"notes":notes},"fingerprint":fingerprint})
    if not rows: raise HTTPException(400,"CSV has no data rows")
    batch_id=f"imp_{uuid.uuid4().hex}"
    batch={"batch_id":batch_id,"import_type":"expenses","status":"awaiting_confirmation" if all(r["valid"] for r in rows) else "invalid_rows","file_name":re.sub(r"[^\w .-]","_",file_name)[:120],"row_count":len(rows),"valid_row_count":sum(r["valid"] for r in rows),"invalid_row_count":sum(not r["valid"] for r in rows),"created_at":datetime.now().isoformat(),"rows":rows,"created_record_ids":[]}
    seed_service._data.setdefault("import_batches",{})[batch_id]=batch
    return {k:v for k,v in batch.items() if k!="rows"} | {"preview":[{k:v for k,v in r.items() if k!="fingerprint"} for r in rows],"confirmation_required":True}


def get_import_batch(batch_id: str) -> dict:
    batch=seed_service._data.setdefault("import_batches",{}).get(batch_id)
    if not batch: raise HTTPException(404,"Import batch not found")
    return {k:v for k,v in batch.items() if k!="rows"} | {"preview":[{k:v for k,v in r.items() if k!="fingerprint"} for r in batch["rows"]]}


def confirm_import(batch_id: str) -> dict:
    batch=seed_service._data.setdefault("import_batches",{}).get(batch_id)
    if not batch: raise HTTPException(404,"Import batch not found")
    if batch["status"]=="completed": return get_import_batch(batch_id)
    if batch["status"]!="awaiting_confirmation" or batch["invalid_row_count"]: raise HTTPException(409,"Correct all invalid rows by uploading a new preview batch before confirmation")
    created=[]
    try:
        for row in batch["rows"]:
            payload=ExpenseCreateRequest(**row["normalized"])
            dto=supplier_service.create_expense(payload)
            created.append(dto.id)
            tx=next(t for t in seed_service.get_transactions() if t["id"]==dto.id)
            tx["import_batch_id"]=batch_id; tx["import_row_number"]=row["row_number"]
    except Exception:
        # The demo store cannot provide cross-record transactions; compensate all newly created rows.
        txs=seed_service.get_transactions(); created_set=set(created)
        for tx in list(txs):
            if tx.get("import_batch_id")==batch_id or tx["id"] in created_set:
                if tx["direction"]=="outflow": seed_service.get_business()["opening_cash_paise"]+=tx["amount_paise"]
                txs.remove(tx)
        batch["status"]="failed"; batch["created_record_ids"]=[]; batch["rows"]=[]
        raise HTTPException(500,"Import could not be completed; staged batch can be reviewed and uploaded again")
    batch["status"]="completed"; batch["confirmed_at"]=datetime.now().isoformat(); batch["completed_at"]=datetime.now().isoformat(); batch["created_record_ids"]=created; batch["rows"]=[]
    seed_service._data.setdefault("audit_events",[]).append({"id":f"audit_{uuid.uuid4().hex[:8]}","type":"expense_import_confirmed","source_id":batch_id,"row_count":len(created),"created_at":datetime.now().isoformat()})
    return get_import_batch(batch_id)


def notification_preferences() -> dict:
    return seed_service._data.setdefault("notification_preferences",{"lead_time_days":7,"customer_instalments_enabled":True,"supplier_bills_enabled":True}) | {"timezone":settings.DEFAULT_TIMEZONE,"external_delivery_enabled":False}

def update_notification_preferences(payload: dict) -> dict:
    prefs=seed_service._data.setdefault("notification_preferences",{"lead_time_days":7,"customer_instalments_enabled":True,"supplier_bills_enabled":True})
    if payload.get("lead_time_days") is not None and not 0 <= payload["lead_time_days"] <= 30:
        raise HTTPException(400,"lead_time_days must be between zero and thirty")
    for key,value in payload.items():
        if value is not None: prefs[key]=value
    return notification_preferences()
