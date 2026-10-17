from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class SuggestedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=2, max_length=100)
    type: Literal["customer", "supplier_bill", "budget", "cash_flow", "simulator"]
    target_id: str | None = Field(default=None, max_length=100)


class GroundedExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(min_length=2, max_length=500)
    reasons: list[str] = Field(default_factory=list, max_length=5)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list, max_length=3)
    disclaimer: str = Field(default="This explanation uses recorded data and estimates.", max_length=240)
    source_ids: list[str] = Field(default_factory=list, max_length=20)


class ExplainForecastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    horizon_days: int = Field(default=14, ge=1, le=60)


class SummarizeBusinessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period_days: int = Field(default=7, ge=1, le=31)


class DraftReminderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str = Field(min_length=1, max_length=100)
    installment_id: str | None = Field(default=None, max_length=100)
    context: str = Field(default="", max_length=300)


class ImportPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    import_type: Literal["expenses"] = "expenses"
    file_name: str = Field(min_length=1, max_length=120)
    csv_text: str = Field(min_length=1, max_length=1_000_000)


class NotificationPreferencesPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lead_time_days: int | None = Field(default=None, ge=0, le=30)
    customer_instalments_enabled: bool | None = None
    supplier_bills_enabled: bool | None = None


class ReminderDraftResponse(BaseModel):
    mode: Literal["ai_draft", "template_fallback"]
    message: str = Field(max_length=500)
    requires_merchant_review: bool = True
    sent: bool = False
    due_date: str | None = None
    remaining_amount_paise: int

