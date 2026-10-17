import copy
from typing import Any, Dict, List
from app.core.database import get_db
from app.core.tenant_context import get_business_id
from app.core.tenant_data import FirestoreTenantData

DEFAULT_SEED_DATA: Dict[str, Any] = {
    "business": {
        "id": "biz_demo_kirana",
        "name": "Demo Kirana Store",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "opening_cash_paise": 1500000,  # ₹15,000
        "cash_safety_buffer_paise": 1500000,  # ₹15,000
        "is_demo": True,
    },
    "customers": [
        {
            "id": "cust_ravi",
            "name": "Ravi Stores",
            "phone": "+91 98765 43210",
            "outstanding_balance_paise": 5000000,  # ₹50,000
            "total_credit_paise": 5000000,
            "total_repaid_paise": 0,
            "last_activity_date": "2026-10-17",
            "is_active": True,
            "credit_entries": [
                {
                    "id": "entry_ravi_1",
                    "entry_type": "credit_sale",
                    "amount_paise": 5000000,
                    "effective_date": "2026-10-17",
                    "due_date": "2026-10-22",
                    "notes": "Bulk pulses and edible oil purchase",
                }
            ],
        },
        {
            "id": "cust_sharma",
            "name": "Sharma General Store",
            "phone": "+91 98111 22334",
            "outstanding_balance_paise": 2000000,  # ₹20,000
            "total_credit_paise": 3000000,
            "total_repaid_paise": 1000000,
            "last_activity_date": "2026-10-16",
            "is_active": True,
            "credit_entries": [
                {
                    "id": "entry_sharma_1",
                    "entry_type": "credit_sale",
                    "amount_paise": 2000000,
                    "effective_date": "2026-10-15",
                    "due_date": "2026-10-24",
                    "notes": "Packaged spices and toiletries",
                }
            ],
        },
        {
            "id": "cust_lakshmi",
            "name": "Lakshmi Provisions",
            "phone": "+91 94444 55667",
            "outstanding_balance_paise": 1450000,  # ₹14,500
            "total_credit_paise": 1450000,
            "total_repaid_paise": 0,
            "last_activity_date": "2026-10-17",
            "is_active": True,
            "credit_entries": [
                {
                    "id": "entry_lakshmi_1",
                    "entry_type": "credit_sale",
                    "amount_paise": 1450000,
                    "effective_date": "2026-10-17",
                    "due_date": "2026-10-26",
                    "notes": "Dairy and confectionery stock",
                }
            ],
        },
    ],
    "suppliers": [
        {
            "id": "sup_coastal",
            "name": "Coastal Wholesale",
            "phone": "+91 80000 11223",
            "is_active": True,
        },
        {
            "id": "sup_metro",
            "name": "Metro FMCG Distributors",
            "phone": "+91 80000 44556",
            "is_active": True,
        },
    ],
    "supplier_bills": [
        {
            "id": "bill_coastal_101",
            "supplier_id": "sup_coastal",
            "supplier_name": "Coastal Wholesale",
            "description": "Edible oil and grains restock invoice #CW-882",
            "bill_amount_paise": 2500000,  # ₹25,000
            "paid_amount_paise": 0,
            "remaining_amount_paise": 2500000,
            "bill_date": "2026-10-17",
            "due_date": "2026-10-20",  # Due 20 Oct before Ravi repayment!
            "status": "unpaid",
        },
        {
            "id": "bill_metro_204",
            "supplier_id": "sup_metro",
            "supplier_name": "Metro FMCG Distributors",
            "description": "Soap, detergent, and oral care products",
            "bill_amount_paise": 1200000,  # ₹12,000
            "paid_amount_paise": 0,
            "remaining_amount_paise": 1200000,
            "bill_date": "2026-10-16",
            "due_date": "2026-10-25",
            "status": "unpaid",
        },
    ],
    "transactions": [
        {
            "id": "tx_open_01",
            "type": "opening_balance",
            "description": "Cash in hand opening register",
            "amount_paise": 1500000,
            "date": "2026-10-17",
            "direction": "inflow",
            "payment_method": "cash",
        },
        {
            "id": "tx_exp_01",
            "type": "expense",
            "category": "utilities",
            "description": "Shop Electricity Bill (Oct)",
            "amount_paise": 125000,  # ₹1,250
            "date": "2026-10-17",
            "direction": "outflow",
            "payment_method": "cash",
        },
        {
            "id": "tx_rep_01",
            "type": "repayment",
            "description": "Sharma General Store partial repayment",
            "amount_paise": 1000000,  # ₹10,000
            "date": "2026-10-16",
            "direction": "inflow",
            "payment_method": "cash",
        },
    ],
    "repayment_plans": [],
    "budgets": [],
    "reminders": {},
    "audit_events": [],
    "ai_interaction_logs": [],
    "import_batches": {},
    "notification_preferences": {"lead_time_days": 7, "customer_instalments_enabled": True, "supplier_bills_enabled": True},
}


class SeedService:
    def __init__(self):
        self._memory_data = copy.deepcopy(DEFAULT_SEED_DATA)
        self._tenant_memory = {"biz_demo_kirana": self._memory_data}

    @property
    def _data(self):
        db = get_db()
        if db.mode in ("firestore", "emulator"):
            return FirestoreTenantData(db, get_business_id())
        return self._tenant_memory.setdefault(get_business_id(), self._empty_business_data(get_business_id()))

    @_data.setter
    def _data(self, value):
        self._memory_data = value
        self._tenant_memory = {"biz_demo_kirana": value}

    @staticmethod
    def _empty_business_data(business_id: str):
        data = copy.deepcopy(DEFAULT_SEED_DATA)
        data["business"] = {
            "id": business_id, "name": "", "currency": "INR", "timezone": "Asia/Kolkata",
            "opening_cash_paise": 0, "cash_safety_buffer_paise": 1500000, "is_demo": False,
        }
        for key in ("customers", "suppliers", "supplier_bills", "transactions", "repayment_plans", "budgets", "audit_events", "ai_interaction_logs"):
            data[key] = []
        data["reminders"] = {}
        data["import_batches"] = {}
        data["scenarios"] = {}
        data["notification_preferences"] = copy.deepcopy(DEFAULT_SEED_DATA["notification_preferences"])
        return data

    def add_memory_business(self, business: dict):
        business_id = business["id"]
        self._memory_data.setdefault("businesses", {})[business_id] = business
        data = self._tenant_memory.setdefault(business_id, self._empty_business_data(business_id))
        data["business"] = business

    def reset(self):
        """Reset demo data to canonical factory default."""
        db = get_db()
        if db.mode in ("firestore", "emulator"):
            tenant = FirestoreTenantData(db, "biz_demo_kirana")
            for field, value in DEFAULT_SEED_DATA.items():
                if field == "business":
                    tenant[field] = {**copy.deepcopy(value), "id": "biz_demo_kirana"}
                elif field in {"customers", "suppliers", "supplier_bills", "transactions", "repayment_plans", "budgets", "audit_events", "ai_interaction_logs"}:
                    collection = db.business_collection("biz_demo_kirana", "cash_events" if field == "transactions" else field)
                    for doc in collection.stream(): doc.reference.delete()
                    for row in value:
                        collection.document(row["id"]).set(copy.deepcopy(row))
                elif field in {"reminders", "import_batches", "scenarios"}:
                    collection = db.business_collection("biz_demo_kirana", field)
                    for doc in collection.stream(): doc.reference.delete()
            tenant["notification_preferences"] = copy.deepcopy(DEFAULT_SEED_DATA["notification_preferences"])
        else:
            self._memory_data = copy.deepcopy(DEFAULT_SEED_DATA)
            self._tenant_memory = {"biz_demo_kirana": self._memory_data}
        return {"status": "ok", "message": "Demo seed data successfully reset to factory defaults."}

    def get_business(self):
        try:
            return self._data["business"]
        except KeyError:
            if get_db().mode in ("firestore", "emulator"):
                return {}
            raise

    def get_customers(self):
        return self._data["customers"]

    def get_supplier_bills(self):
        return self._data["supplier_bills"]

    def get_transactions(self):
        return self._data["transactions"]


# Global seed service instance for Phase 1 demo/development mode
seed_service = SeedService()
