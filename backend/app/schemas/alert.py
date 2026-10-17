from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertContributorDTO(BaseModel):
    source_type: str  # 'supplier_bill', 'customer_collection', 'expense'
    source_id: str
    description: str
    amount_paise: int
    direction: str  # 'outflow' or 'inflow'


class CashAlertDTO(BaseModel):
    id: str
    type: str  # 'cash_shortage' | 'safety_buffer_breach'
    severity: str  # 'critical' | 'warning'
    title: str
    message: str
    breach_date: str
    projected_balance_paise: int
    threshold_paise: int
    deficit_paise: int  # How much below threshold
    acknowledged: bool = False
    contributing_events: List[AlertContributorDTO] = Field(default_factory=list)
    suggested_action: str
    created_at: str


class AlertAcknowledgeRequest(BaseModel):
    acknowledged: bool = True


class AlertsListResponse(BaseModel):
    active_count: int
    critical_count: int
    warning_count: int
    alerts: List[CashAlertDTO]
