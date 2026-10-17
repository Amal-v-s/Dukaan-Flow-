from typing import List, Literal, Optional
from pydantic import BaseModel


class ForecastSummary(BaseModel):
    horizon_days: int = 14
    lowest_balance_paise: int
    lowest_balance_date: str
    has_shortage: bool
    safety_buffer_breach: bool


class RecentTransactionDTO(BaseModel):
    id: str
    type: str
    description: str
    amount_paise: int
    date: str
    direction: Literal["inflow", "outflow"]
    payment_method: str = "cash"


class UpcomingItemDTO(BaseModel):
    id: str
    title: str
    entity_type: Literal["customer_due", "supplier_bill", "expense"]
    amount_paise: int
    due_date: str
    status: str


class DashboardResponse(BaseModel):
    currency: str = "INR"
    available_cash_paise: int
    receivables_paise: int
    payables_paise: int
    today_income_paise: int = 0
    today_expenses_paise: int = 0
    forecast: ForecastSummary
    recent_transactions: List[RecentTransactionDTO]
    upcoming_items: List[UpcomingItemDTO]
