from typing import Optional
from fastapi import APIRouter
from app.schemas.supplier import ExpenseCreateRequest, ExpenseDTO, ExpenseListResponse
from app.services.supplier_service import supplier_service

router = APIRouter(prefix="/api/v1", tags=["Expenses"])


@router.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(category: Optional[str] = None):
    """List operational shop expenses."""
    items = supplier_service.list_expenses(category=category)
    return ExpenseListResponse(items=items, total_count=len(items))


@router.post("/expenses", response_model=ExpenseDTO, status_code=201)
def create_expense(req: ExpenseCreateRequest):
    """Record an operational expense (utilities, rent, repairs, etc.).
    
    Paid expenses record an immediate cash outflow and deduct from available cash.
    """
    return supplier_service.create_expense(req)
