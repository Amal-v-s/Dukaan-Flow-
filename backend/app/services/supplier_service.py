import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from app.schemas.supplier import (
    ExpenseCreateRequest,
    ExpenseDTO,
    SupplierBillCreateRequest,
    SupplierBillDTO,
    SupplierCreateRequest,
    SupplierDTO,
    SupplierPaymentCreateRequest,
    SupplierPaymentDTO,
)
from app.services.seed_data import seed_service
from app.core.tenant_context import get_business_id, get_user_id


class SupplierService:
    def list_suppliers(self) -> List[SupplierDTO]:
        data = seed_service._data.get("suppliers", [])
        return [
            SupplierDTO(
                id=s["id"],
                name=s["name"],
                phone=s.get("phone"),
                notes=s.get("notes", ""),
                is_active=s.get("is_active", True),
            )
            for s in data
        ]

    def create_supplier(self, req: SupplierCreateRequest) -> SupplierDTO:
        suppliers = seed_service._data.get("suppliers", [])
        new_id = f"sup_{uuid.uuid4().hex[:8]}"
        new_sup = {
            "id": new_id,
            "name": req.name.strip(),
            "phone": req.phone.strip() if req.phone else None,
            "notes": req.notes or "",
            "is_active": True,
        }
        suppliers.append(new_sup)
        return SupplierDTO(
            id=new_sup["id"],
            name=new_sup["name"],
            phone=new_sup["phone"],
            notes=new_sup["notes"],
            is_active=True,
        )

    def list_supplier_bills(self, status: Optional[str] = None, supplier_id: Optional[str] = None) -> List[SupplierBillDTO]:
        bills = seed_service.get_supplier_bills()
        result: List[SupplierBillDTO] = []
        for b in bills:
            if status and b["status"] != status:
                continue
            if supplier_id and b.get("supplier_id") != supplier_id:
                continue
            result.append(
                SupplierBillDTO(
                    id=b["id"],
                    supplier_id=b.get("supplier_id", ""),
                    supplier_name=b["supplier_name"],
                    description=b["description"],
                    bill_amount_paise=b["bill_amount_paise"],
                    paid_amount_paise=b["paid_amount_paise"],
                    remaining_amount_paise=b["remaining_amount_paise"],
                    bill_date=b["bill_date"],
                    due_date=b["due_date"],
                    status=b["status"],
                    created_at=b.get("created_at", b["bill_date"]),
                )
            )
        # Sort by due_date ascending
        result.sort(key=lambda x: x.due_date)
        return result

    def create_supplier_bill(self, req: SupplierBillCreateRequest) -> SupplierBillDTO:
        suppliers = seed_service._data.get("suppliers", [])
        supplier = next((s for s in suppliers if s["id"] == req.supplier_id), None)
        supplier_name = supplier["name"] if supplier else "Wholesale Supplier"

        bills = seed_service.get_supplier_bills()
        new_id = f"bill_{uuid.uuid4().hex[:8]}"
        today = datetime.now().strftime("%Y-%m-%d")

        new_bill = {
            "id": new_id,
            "supplier_id": req.supplier_id,
            "supplier_name": supplier_name,
            "description": req.description.strip(),
            "bill_amount_paise": req.bill_amount_paise,
            "paid_amount_paise": 0,
            "remaining_amount_paise": req.bill_amount_paise,
            "bill_date": req.bill_date,
            "due_date": req.due_date,
            "status": "unpaid",
            "created_at": today,
            "payments": [],
        }

        bills.append(new_bill)

        return SupplierBillDTO(
            id=new_bill["id"],
            supplier_id=new_bill["supplier_id"],
            supplier_name=new_bill["supplier_name"],
            description=new_bill["description"],
            bill_amount_paise=new_bill["bill_amount_paise"],
            paid_amount_paise=0,
            remaining_amount_paise=new_bill["remaining_amount_paise"],
            bill_date=new_bill["bill_date"],
            due_date=new_bill["due_date"],
            status="unpaid",
            created_at=today,
        )

    def pay_supplier_bill(self, bill_id: str, req: SupplierPaymentCreateRequest) -> SupplierPaymentDTO:
        bills = seed_service.get_supplier_bills()
        bill = next((b for b in bills if b["id"] == bill_id), None)
        if not bill:
            raise HTTPException(status_code=404, detail="Supplier bill not found")

        remaining = bill["remaining_amount_paise"]
        if req.amount_paise > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount ({req.amount_paise} paise) exceeds remaining bill due ({remaining} paise)",
            )

        # Update bill amounts
        bill["paid_amount_paise"] += req.amount_paise
        bill["remaining_amount_paise"] -= req.amount_paise

        if bill["remaining_amount_paise"] == 0:
            bill["status"] = "paid"
        else:
            bill["status"] = "partially_paid"

        payment_id = f"spay_{uuid.uuid4().hex[:8]}"
        payment = {
            "id": payment_id,
            "bill_id": bill_id,
            "supplier_id": bill.get("supplier_id", ""),
            "amount_paise": req.amount_paise,
            "payment_date": req.payment_date,
            "payment_method": req.payment_method or "cash",
            "notes": req.notes or "",
            "created_at": datetime.now().isoformat(),
        }

        if "payments" not in bill:
            bill["payments"] = []
        bill["payments"].append(payment)

        # Synchronize cash outflow: add to cashbook transactions and deduct from register cash
        txs = seed_service.get_transactions()
        txs.append({
            "id": f"tx_spay_{uuid.uuid4().hex[:8]}",
            "type": "supplier_payment",
            "description": f"Paid {bill['supplier_name']} - {bill['description']}",
            "amount_paise": req.amount_paise,
            "date": req.payment_date,
            "direction": "outflow",
            "payment_method": req.payment_method or "cash",
        })

        biz = seed_service.get_business()
        biz["opening_cash_paise"] -= req.amount_paise
        from app.services.audit_service import audit_service
        audit_service.log_event(
            business_id=get_business_id(),
            actor_id=get_user_id(),
            action="supplier_payment_recorded",
            entity_type="supplier_bill",
            entity_id=bill_id,
            metadata={"payment_id": payment_id, "amount_paise": req.amount_paise, "payment_date": req.payment_date},
        )

        return SupplierPaymentDTO(
            id=payment["id"],
            bill_id=payment["bill_id"],
            supplier_id=payment["supplier_id"],
            amount_paise=payment["amount_paise"],
            payment_date=payment["payment_date"],
            payment_method=payment["payment_method"],
            notes=payment["notes"],
            created_at=payment["created_at"],
        )

    def list_expenses(self, category: Optional[str] = None) -> List[ExpenseDTO]:
        txs = seed_service.get_transactions()
        expenses: List[ExpenseDTO] = []
        for t in txs:
            if t["type"] == "expense":
                if category and t.get("category") != category:
                    continue
                expenses.append(
                    ExpenseDTO(
                        id=t["id"],
                        title=t["description"],
                        category=t.get("category", "misc"),
                        amount_paise=t["amount_paise"],
                        expense_date=t["date"],
                        payment_status="paid",
                        payment_method=t.get("payment_method", "cash"),
                        notes="",
                        created_at=t["date"],
                    )
                )
        return expenses

    def create_expense(self, req: ExpenseCreateRequest) -> ExpenseDTO:
        txs = seed_service.get_transactions()
        expense_id = f"exp_{uuid.uuid4().hex[:8]}"

        # Record into transactions as cash outflow
        txs.append({
            "id": expense_id,
            "type": "expense",
            "category": req.category,
            "description": req.title.strip(),
            "amount_paise": req.amount_paise,
            "date": req.expense_date,
            "direction": "outflow",
            "payment_method": req.payment_method or "cash",
        })

        # Deduct immediately from shop available cash
        biz = seed_service.get_business()
        biz["opening_cash_paise"] -= req.amount_paise

        return ExpenseDTO(
            id=expense_id,
            title=req.title.strip(),
            category=req.category,
            amount_paise=req.amount_paise,
            expense_date=req.expense_date,
            payment_status="paid",
            payment_method=req.payment_method or "cash",
            notes=req.notes or "",
            created_at=datetime.now().isoformat(),
        )


supplier_service = SupplierService()
