from datetime import date
from typing import List
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.domain.forecast import generate_forecast
from app.services.seed_data import seed_service

router = APIRouter(prefix="/api/v1/cash-flow", tags=["Cash Flow Forecast"])


class ForecastContributorDTO(BaseModel):
    source_type: str
    source_id: str
    description: str
    amount_paise: int


class ForecastDayDTO(BaseModel):
    date: str
    opening_balance_paise: int
    inflows_paise: int
    outflows_paise: int
    closing_balance_paise: int
    below_zero: bool
    below_safety_buffer: bool
    contributors: List[ForecastContributorDTO]


class CashFlowForecastResponse(BaseModel):
    currency: str = "INR"
    horizon_days: int
    cash_safety_buffer_paise: int
    lowest_dip_paise: int
    lowest_dip_date: str
    shortage_detected: bool
    buffer_breached: bool
    days: List[ForecastDayDTO]
    assumptions: List[str]


@router.get("/forecast", response_model=CashFlowForecastResponse)
def get_forecast(horizon_days: int = Query(default=14, ge=1, le=60)):
    biz = seed_service.get_business()
    customers = seed_service.get_customers()
    bills = seed_service.get_supplier_bills()

    start_date = date.fromisoformat("2026-10-17")
    safety_buffer = biz.get("cash_safety_buffer_paise", 1500000)

    # Gather future customer collections (inflows)
    inflows = []
    for c in customers:
        for entry in c.get("credit_entries", []):
            if entry.get("status", "posted") == "posted" and entry.get("entry_type") == "credit_sale":
                d = entry.get("due_date")
                if d:
                    inflows.append({
                        "date": d,
                        "amount_paise": entry["amount_paise"],
                        "source_type": "customer_collection",
                        "source_id": entry["id"],
                        "description": f"{c['name']} (Repayment due)",
                    })

    # Gather scheduled future supplier bills (outflows)
    outflows = []
    for b in bills:
        remaining = b.get("remaining_amount_paise", 0)
        if remaining > 0 and b.get("status") != "paid":
            d = b.get("due_date")
            if d:
                outflows.append({
                    "date": d,
                    "amount_paise": remaining,
                    "source_type": "supplier_bill",
                    "source_id": b["id"],
                    "description": f"{b['supplier_name']} - {b['description']}",
                })

    # Execute pure deterministic domain forecast engine
    result = generate_forecast(
        start_date=start_date,
        opening_cash_paise=biz["opening_cash_paise"],
        inflows=inflows,
        outflows=outflows,
        safety_buffer_paise=safety_buffer,
        horizon_days=horizon_days,
    )

    day_dtos = [
        ForecastDayDTO(
            date=day.date,
            opening_balance_paise=day.opening_balance_paise,
            inflows_paise=day.inflows_paise,
            outflows_paise=day.outflows_paise,
            closing_balance_paise=day.closing_balance_paise,
            below_zero=day.below_zero,
            below_safety_buffer=day.below_safety_buffer,
            contributors=[
                ForecastContributorDTO(
                    source_type=c.source_type,
                    source_id=c.source_id,
                    description=c.description,
                    amount_paise=c.amount_paise,
                )
                for c in day.contributors
            ],
        )
        for day in result.days
    ]

    return CashFlowForecastResponse(
        currency="INR",
        horizon_days=result.horizon_days,
        cash_safety_buffer_paise=result.safety_buffer_paise,
        lowest_dip_paise=result.lowest_dip_paise,
        lowest_dip_date=result.lowest_dip_date,
        shortage_detected=result.shortage_detected,
        buffer_breached=result.buffer_breached,
        days=day_dtos,
        assumptions=result.assumptions,
    )
