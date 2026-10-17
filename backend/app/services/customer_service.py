import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from app.domain.ledger import calculate_customer_balance, validate_repayment_amount
from app.schemas.customer import (
    CustomerCreateRequest,
    CustomerDTO,
    CustomerLedgerResponse,
    CustomerUpdateRequest,
    LedgerEntryCreateRequest,
    LedgerEntryDTO,
)
from app.services.seed_data import seed_service
from app.services.phase2_service import allocate_unplanned_repayment


class CustomerService:
    def list_customers(self, query: Optional[str] = None) -> List[CustomerDTO]:
        customers = seed_service.get_customers()
        result: List[CustomerDTO] = []
        for c in customers:
            if query and query.lower() not in c["name"].lower() and (not c.get("phone") or query not in c["phone"]):
                continue

            # Recalculate balance from canonical entries
            entries = c.get("credit_entries", [])
            outstanding, total_credit, total_repaid = calculate_customer_balance(entries)
            c["outstanding_balance_paise"] = outstanding
            c["total_credit_paise"] = total_credit
            c["total_repaid_paise"] = total_repaid

            result.append(
                CustomerDTO(
                    id=c["id"],
                    name=c["name"],
                    phone=c.get("phone"),
                    notes=c.get("notes", ""),
                    outstanding_balance_paise=outstanding,
                    total_credit_paise=total_credit,
                    total_repaid_paise=total_repaid,
                    last_activity_date=c.get("last_activity_date", "2026-10-17"),
                    is_active=c.get("is_active", True),
                )
            )
        return result

    def get_customer(self, customer_id: str) -> CustomerDTO:
        customers = seed_service.get_customers()
        c = next((item for item in customers if item["id"] == customer_id), None)
        if not c:
            raise HTTPException(status_code=404, detail="Customer not found")

        entries = c.get("credit_entries", [])
        outstanding, total_credit, total_repaid = calculate_customer_balance(entries)
        c["outstanding_balance_paise"] = outstanding
        c["total_credit_paise"] = total_credit
        c["total_repaid_paise"] = total_repaid

        return CustomerDTO(
            id=c["id"],
            name=c["name"],
            phone=c.get("phone"),
            notes=c.get("notes", ""),
            outstanding_balance_paise=outstanding,
            total_credit_paise=total_credit,
            total_repaid_paise=total_repaid,
            last_activity_date=c.get("last_activity_date", "2026-10-17"),
            is_active=c.get("is_active", True),
        )

    def create_customer(self, req: CustomerCreateRequest) -> CustomerDTO:
        customers = seed_service.get_customers()
        new_id = f"cust_{uuid.uuid4().hex[:8]}"
        today = datetime.now().strftime("%Y-%m-%d")

        new_customer = {
            "id": new_id,
            "name": req.name.strip(),
            "phone": req.phone.strip() if req.phone else None,
            "notes": req.notes or "",
            "outstanding_balance_paise": 0,
            "total_credit_paise": 0,
            "total_repaid_paise": 0,
            "last_activity_date": today,
            "is_active": True,
            "credit_entries": [],
        }
        customers.append(new_customer)

        return CustomerDTO(
            id=new_customer["id"],
            name=new_customer["name"],
            phone=new_customer["phone"],
            notes=new_customer["notes"],
            outstanding_balance_paise=0,
            total_credit_paise=0,
            total_repaid_paise=0,
            last_activity_date=today,
            is_active=True,
        )

    def update_customer(self, customer_id: str, req: CustomerUpdateRequest) -> CustomerDTO:
        customers = seed_service.get_customers()
        c = next((item for item in customers if item["id"] == customer_id), None)
        if not c:
            raise HTTPException(status_code=404, detail="Customer not found")

        if req.name is not None:
            c["name"] = req.name.strip()
        if req.phone is not None:
            c["phone"] = req.phone.strip() if req.phone else None
        if req.notes is not None:
            c["notes"] = req.notes
        if req.is_active is not None:
            c["is_active"] = req.is_active

        return self.get_customer(customer_id)

    def get_customer_ledger(self, customer_id: str) -> CustomerLedgerResponse:
        customer_dto = self.get_customer(customer_id)
        customers = seed_service.get_customers()
        c = next(item for item in customers if item["id"] == customer_id)

        entries_dto: List[LedgerEntryDTO] = []
        for entry in c.get("credit_entries", []):
            entries_dto.append(
                LedgerEntryDTO(
                    id=entry["id"],
                    customer_id=customer_id,
                    entry_type=entry["entry_type"],
                    amount_paise=entry["amount_paise"],
                    effective_date=entry["effective_date"],
                    due_date=entry.get("due_date"),
                    status=entry.get("status", "posted"),
                    payment_method=entry.get("payment_method", "cash"),
                    notes=entry.get("notes", ""),
                    created_at=entry.get("created_at", entry["effective_date"]),
                )
            )

        # Sort entries chronologically descending
        entries_dto.sort(key=lambda x: x.effective_date, reverse=True)
        return CustomerLedgerResponse(customer=customer_dto, entries=entries_dto)

    def add_ledger_entry(self, customer_id: str, req: LedgerEntryCreateRequest) -> LedgerEntryDTO:
        customers = seed_service.get_customers()
        c = next((item for item in customers if item["id"] == customer_id), None)
        if not c:
            raise HTTPException(status_code=404, detail="Customer not found")

        entries = c.get("credit_entries", [])
        current_outstanding, _, _ = calculate_customer_balance(entries)

        if req.entry_type == "repayment":
            try:
                validate_repayment_amount(current_outstanding, req.amount_paise)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        entry_id = f"entry_{uuid.uuid4().hex[:8]}"
        new_entry = {
            "id": entry_id,
            "customer_id": customer_id,
            "entry_type": req.entry_type,
            "amount_paise": req.amount_paise,
            "effective_date": req.effective_date,
            "due_date": req.due_date if req.entry_type == "credit_sale" else None,
            "status": "posted",
            "payment_method": req.payment_method or "cash",
            "notes": req.notes or "",
            "created_at": datetime.now().isoformat(),
        }

        entries.append(new_entry)
        c["last_activity_date"] = req.effective_date

        if req.entry_type == "repayment":
            allocate_unplanned_repayment(customer_id, req.amount_paise, req.effective_date)

        # Recalculate balance
        outstanding, total_credit, total_repaid = calculate_customer_balance(entries)
        c["outstanding_balance_paise"] = outstanding
        c["total_credit_paise"] = total_credit
        c["total_repaid_paise"] = total_repaid

        # If repayment, synchronize into cash book as an inflow and increase available cash
        if req.entry_type == "repayment":
            txs = seed_service.get_transactions()
            tx_id = f"tx_rep_{uuid.uuid4().hex[:8]}"
            txs.append({
                "id": tx_id,
                "type": "repayment",
                "description": f"{c['name']} repayment: {req.notes or 'Khata collection'}",
                "amount_paise": req.amount_paise,
                "date": req.effective_date,
                "direction": "inflow",
                "payment_method": req.payment_method or "cash",
            })
            # Increase available cash in business register
            biz = seed_service.get_business()
            biz["opening_cash_paise"] += req.amount_paise

        return LedgerEntryDTO(
            id=new_entry["id"],
            customer_id=customer_id,
            entry_type=new_entry["entry_type"],
            amount_paise=new_entry["amount_paise"],
            effective_date=new_entry["effective_date"],
            due_date=new_entry["due_date"],
            status="posted",
            payment_method=new_entry["payment_method"],
            notes=new_entry["notes"],
            created_at=new_entry["created_at"],
        )


customer_service = CustomerService()
