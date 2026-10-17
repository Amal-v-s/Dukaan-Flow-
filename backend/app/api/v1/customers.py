from typing import Optional
from fastapi import APIRouter
from app.schemas.customer import (
    CustomerCreateRequest,
    CustomerDTO,
    CustomerLedgerResponse,
    CustomerListResponse,
    CustomerUpdateRequest,
    LedgerEntryCreateRequest,
    LedgerEntryDTO,
    LedgerEntryReversalRequest,
)
from app.services.customer_service import customer_service

router = APIRouter(prefix="/api/v1", tags=["Customers"])


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(query: Optional[str] = None):
    """List all customers with optional name/phone query filter."""
    items = customer_service.list_customers(query)
    return CustomerListResponse(items=items, total_count=len(items))


@router.post("/customers", response_model=CustomerDTO, status_code=201)
def create_customer(req: CustomerCreateRequest):
    """Create a new customer credit account."""
    return customer_service.create_customer(req)


@router.get("/customers/{customer_id}", response_model=CustomerDTO)
def get_customer(customer_id: str):
    """Get single customer profile with current calculated balance."""
    return customer_service.get_customer(customer_id)


@router.patch("/customers/{customer_id}", response_model=CustomerDTO)
def update_customer(customer_id: str, req: CustomerUpdateRequest):
    """Update customer details."""
    return customer_service.update_customer(customer_id, req)


@router.get("/customers/{customer_id}/ledger", response_model=CustomerLedgerResponse)
def get_customer_ledger(customer_id: str):
    """Retrieve full customer profile and chronological ledger entries."""
    return customer_service.get_customer_ledger(customer_id)


@router.post("/customers/{customer_id}/ledger-entries", response_model=LedgerEntryDTO, status_code=201)
def add_ledger_entry(customer_id: str, req: LedgerEntryCreateRequest):
    """Record a credit sale or repayment on the customer's ledger.
    
    If repayment:
    - Validates that repayment does not exceed outstanding balance.
    - Synchronizes the received funds into the shop cash book and increases available cash.
    """
    return customer_service.add_ledger_entry(customer_id, req)


@router.post("/customers/{customer_id}/ledger-entries/reversals", response_model=LedgerEntryDTO, status_code=201)
def reverse_ledger_entry(customer_id: str, req: LedgerEntryReversalRequest):
    """Create a non-destructive audit-backed reversal adjustment for an existing ledger entry."""
    return customer_service.reverse_ledger_entry(
        customer_id=customer_id,
        entry_id=req.entry_id,
        reason=req.reason,
    )
