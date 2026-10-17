from typing import List, Optional
from pydantic import BaseModel, Field


class ScenarioEventCreate(BaseModel):
    event_type: str = Field(..., description="customer_collection | supplier_bill | extra_expense | extra_income")
    source_id: Optional[str] = Field(default=None, description="ID of existing bill/entry being modified, or None for new hypothetical")
    amount_paise: int = Field(..., ge=0, description="Amount in integer paise")
    original_date: Optional[str] = Field(default=None, description="Original ISO date if modifying existing event")
    scenario_date: str = Field(..., description="Hypothetical ISO date")
    description: Optional[str] = Field(default="", description="Description of the hypothetical change")


class ScenarioEventDTO(ScenarioEventCreate):
    id: str


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default="")
    events: List[ScenarioEventCreate] = Field(default_factory=list)


class ScenarioDTO(BaseModel):
    id: str
    name: str
    description: str
    events: List[ScenarioEventDTO]
    created_at: str


class ScenarioForecastDayDTO(BaseModel):
    date: str
    baseline_closing_paise: int
    scenario_closing_paise: int
    delta_paise: int
    baseline_below_zero: bool
    scenario_below_zero: bool
    baseline_below_buffer: bool
    scenario_below_buffer: bool


class ScenarioForecastResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    currency: str = "INR"
    horizon_days: int
    safety_buffer_paise: int
    baseline_lowest_dip_paise: int
    baseline_lowest_dip_date: str
    baseline_has_shortage: bool
    scenario_lowest_dip_paise: int
    scenario_lowest_dip_date: str
    scenario_has_shortage: bool
    net_improvement_paise: int
    shortage_resolved: bool
    days: List[ScenarioForecastDayDTO]
