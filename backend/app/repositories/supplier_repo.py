"""Supplier and Bills Repository."""
from typing import Any, Dict, List, Optional
from app.core.database import get_db
from app.services.seed_data import seed_service


class SupplierRepository:
    def __init__(self):
        self.db = get_db()

    def list_suppliers(self, business_id: str) -> List[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            docs = self.db.business_collection(business_id, "suppliers").get()
            return [d.to_dict() for d in docs if d.exists]
        return seed_service._data.get("suppliers", [])

    def list_bills(self, business_id: str) -> List[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            docs = self.db.business_collection(business_id, "supplier_bills").get()
            return [d.to_dict() for d in docs if d.exists]
        return seed_service.get_supplier_bills()

    def get_bill(self, business_id: str, bill_id: str) -> Optional[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            doc = self.db.business_collection(business_id, "supplier_bills").document(bill_id).get()
            return doc.to_dict() if doc.exists else None
        bills = seed_service.get_supplier_bills()
        return next((b for b in bills if b["id"] == bill_id), None)

    def save_bill(self, business_id: str, bill_data: Dict[str, Any]) -> None:
        if self.db.mode in ("firestore", "emulator"):
            self.db.business_collection(business_id, "supplier_bills").document(bill_data["id"]).set(bill_data)
        else:
            bills = seed_service.get_supplier_bills()
            idx = next((i for i, b in enumerate(bills) if b["id"] == bill_data["id"]), None)
            if idx is not None:
                bills[idx] = bill_data
            else:
                bills.append(bill_data)


supplier_repo = SupplierRepository()
