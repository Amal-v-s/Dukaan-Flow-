from typing import Optional
from fastapi import APIRouter
from app.schemas.supplier import (
    SupplierBillCreateRequest,
    SupplierBillDTO,
    SupplierBillListResponse,
    SupplierCreateRequest,
    SupplierDTO,
    SupplierListResponse,
    SupplierPaymentCreateRequest,
    SupplierPaymentDTO,
)
from app.services.supplier_service import supplier_service

router = APIRouter(prefix="/api/v1", tags=["Suppliers & Bills"])


@router.get("/suppliers", response_model=SupplierListResponse)
def list_suppliers():
    """List all registered wholesale suppliers."""
    items = supplier_service.list_suppliers()
    return SupplierListResponse(items=items, total_count=len(items))


@router.post("/suppliers", response_model=SupplierDTO, status_code=201)
def create_supplier(req: SupplierCreateRequest):
    """Register a new wholesale supplier."""
    return supplier_service.create_supplier(req)


@router.get("/supplier-bills", response_model=SupplierBillListResponse)
def list_supplier_bills(status: Optional[str] = None, supplier_id: Optional[str] = None):
    """List supplier invoices with status and due date filters."""
    items = supplier_service.list_supplier_bills(status=status, supplier_id=supplier_id)
    return SupplierBillListResponse(items=items, total_count=len(items))


@router.post("/supplier-bills", response_model=SupplierBillDTO, status_code=201)
def create_supplier_bill(req: SupplierBillCreateRequest):
    """Record a new supplier bill / inventory purchase payable.
    
    Unpaid bills increase liabilities (payables) and feed the forecast,
    but do not decrease cash until a payment is recorded.
    """
    return supplier_service.create_supplier_bill(req)


@router.post("/supplier-bills/{bill_id}/payments", response_model=SupplierPaymentDTO, status_code=201)
def pay_supplier_bill(bill_id: str, req: SupplierPaymentCreateRequest):
    """Record a partial or full payment toward a supplier bill.
    
    Decreases bill remaining due, advances bill status, and synchronizes
    an outflow in the cash book (reducing available cash).
    """
    return supplier_service.pay_supplier_bill(bill_id, req)
