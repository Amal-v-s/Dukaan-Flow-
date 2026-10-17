"""Business and Store Settings Repository."""
from typing import Any, Dict, Optional
from app.core.database import get_db
from app.services.seed_data import seed_service


class BusinessRepository:
    def __init__(self):
        self.db = get_db()

    def get_business(self, business_id: str) -> Optional[Dict[str, Any]]:
        if self.db.mode in ("firestore", "emulator"):
            doc = self.db.collection("businesses").document(business_id).get()
            return doc.to_dict() if doc.exists else None
        businesses = seed_service._data.get("businesses", {})
        if business_id in businesses:
            return businesses[business_id]
        return seed_service.get_business()

    def update_settings(self, business_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        if self.db.mode in ("firestore", "emulator"):
            self.db.collection("businesses").document(business_id).update(updates)
            return self.get_business(business_id) or {}
        biz = seed_service.get_business()
        biz.update(updates)
        return biz


business_repo = BusinessRepository()
