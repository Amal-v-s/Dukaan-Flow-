"""Customer and Khata Ledger Repository."""
from typing import Any, Dict, List, Optional
from app.core.database import get_db
from app.services.seed_data import seed_service


class CustomerRepository:
    def __init__(self):
        self.db = get_db()

    def list_customers(self, business_id: str) -> List[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            docs = self.db.business_collection(business_id, "customers").get()
            return [d.to_dict() for d in docs if d.exists]
        # In-memory / seed fallback
        return seed_service.get_customers()

    def get_customer(self, business_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            doc = self.db.business_collection(business_id, "customers").document(customer_id).get()
            return doc.to_dict() if doc.exists else None
        customers = seed_service.get_customers()
        return next((c for c in customers if c["id"] == customer_id), None)

    def save_customer(self, business_id: str, customer_data: Dict[str, Any]) -> None:
        if self.db.mode in ("firestore", "emulator"):
            self.db.business_collection(business_id, "customers").document(customer_data["id"]).set(customer_data)
        else:
            customers = seed_service.get_customers()
            idx = next((i for i, c in enumerate(customers) if c["id"] == customer_data["id"]), None)
            if idx is not None:
                customers[idx] = customer_data
            else:
                customers.append(customer_data)


customer_repo = CustomerRepository()
