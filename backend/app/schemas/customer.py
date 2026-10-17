from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class CustomerCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field("", max_length=500)


class CustomerUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class LedgerEntryCreateRequest(BaseModel):
    entry_type: Literal["credit_sale", "repayment"]
    amount_paise: int = Field(..., gt=0, description="Amount in integer paise")
    effective_date: str = Field(..., description="YYYY-MM-DD")
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD (mandatory for credit_sale)")
    payment_method: Optional[str] = Field("cash", description="cash, upi, bank_transfer")
    notes: Optional[str] = Field("", max_length=500)


class LedgerEntryDTO(BaseModel):
    id: str
    customer_id: str
    entry_type: str
    amount_paise: int
    effective_date: str
    due_date: Optional[str] = None
    status: str = "posted"
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = ""
    created_at: str


class CustomerDTO(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    notes: Optional[str] = ""
    outstanding_balance_paise: int
    total_credit_paise: int
    total_repaid_paise: int
    last_activity_date: str
    is_active: bool


class CustomerListResponse(BaseModel):
    items: List[CustomerDTO]
    total_count: int


class CustomerLedgerResponse(BaseModel):
    customer: CustomerDTO
    entries: List[LedgerEntryDTO]
