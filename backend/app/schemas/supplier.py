from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class SupplierCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field("", max_length=500)


class SupplierDTO(BaseModel):
    id: str
    name: str
    phone: Optional[str] = None
    notes: Optional[str] = ""
    is_active: bool = True


class SupplierListResponse(BaseModel):
    items: List[SupplierDTO]
    total_count: int


class SupplierBillCreateRequest(BaseModel):
    supplier_id: str
    description: str = Field(..., min_length=2, max_length=200)
    bill_amount_paise: int = Field(..., gt=0, description="Total invoice amount in paise")
    bill_date: str = Field(..., description="YYYY-MM-DD")
    due_date: str = Field(..., description="YYYY-MM-DD")


class SupplierBillDTO(BaseModel):
    id: str
    supplier_id: str
    supplier_name: str
    description: str
    bill_amount_paise: int
    paid_amount_paise: int
    remaining_amount_paise: int
    bill_date: str
    due_date: str
    status: Literal["unpaid", "partially_paid", "paid"]
    created_at: str


class SupplierBillListResponse(BaseModel):
    items: List[SupplierBillDTO]
    total_count: int


class SupplierPaymentCreateRequest(BaseModel):
    amount_paise: int = Field(..., gt=0, description="Payment amount in paise")
    payment_date: str = Field(..., description="YYYY-MM-DD")
    payment_method: Optional[str] = Field("cash", description="cash, upi, bank_transfer")
    notes: Optional[str] = Field("", max_length=500)


class SupplierPaymentDTO(BaseModel):
    id: str
    bill_id: str
    supplier_id: str
    amount_paise: int
    payment_date: str
    payment_method: str
    notes: Optional[str] = ""
    created_at: str


class ExpenseCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    category: str = Field(..., description="utilities, rent, transport, packaging, repairs, misc")
    amount_paise: int = Field(..., gt=0, description="Amount in integer paise")
    expense_date: str = Field(..., description="YYYY-MM-DD")
    payment_method: Optional[str] = Field("cash", description="cash, upi, bank_transfer")
    notes: Optional[str] = Field("", max_length=500)


class ExpenseDTO(BaseModel):
    id: str
    title: str
    category: str
    amount_paise: int
    expense_date: str
    payment_status: str = "paid"
    payment_method: str = "cash"
    notes: Optional[str] = ""
    created_at: str


class ExpenseListResponse(BaseModel):
    items: List[ExpenseDTO]
    total_count: int
