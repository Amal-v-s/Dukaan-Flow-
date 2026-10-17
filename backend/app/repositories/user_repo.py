"""Persistent users, email index, and business membership records."""
import hashlib
from typing import Optional

from app.core.database import get_db
from app.services.seed_data import DEFAULT_SEED_DATA, seed_service


class UserRepository:
    def __init__(self):
        self.db = get_db()

    @staticmethod
    def email_key(email: str) -> str:
        return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()

    def get_by_id(self, user_id: str) -> Optional[dict]:
        if self.db.mode in ("firestore", "emulator"):
            snap = self.db.collection("users").document(user_id).get()
            return snap.to_dict() if snap.exists else None
        return next((u for u in seed_service._memory_data.setdefault("users", []) if u["id"] == user_id), None)

    def get_by_email(self, email: str) -> Optional[dict]:
        normalized = email.strip().lower()
        if self.db.mode in ("firestore", "emulator"):
            index = self.db.collection("user_email_index").document(self.email_key(normalized)).get()
            if not index.exists:
                return None
            return self.get_by_id((index.to_dict() or {}).get("user_id", ""))
        return next((u for u in seed_service._memory_data.setdefault("users", []) if u["email"].lower() == normalized), None)

    def create_account(self, user: dict, business: dict) -> None:
        if self.db.mode not in ("firestore", "emulator"):
            users = seed_service._memory_data.setdefault("users", [])
            if any(u["email"].lower() == user["email"].lower() for u in users):
                raise ValueError("duplicate_email")
            users.append(user)
            seed_service.add_memory_business(business)
            return

        client = self.db.firestore_client
        email_ref = self.db.collection("user_email_index").document(self.email_key(user["email"]))
        user_ref = self.db.collection("users").document(user["id"])
        business_ref = self.db.business_document(business["id"])
        member_ref = self.db.business_collection(business["id"], "members").document(user["id"])
        preferences_ref = self.db.business_collection(business["id"], "settings").document("notification_preferences")
        transaction = client.transaction()
        existing = email_ref.get(transaction=transaction)
        if existing.exists:
            raise ValueError("duplicate_email")
        transaction.create(email_ref, {"user_id": user["id"], "email": user["email"].lower()})
        transaction.create(user_ref, user)
        transaction.create(business_ref, business)
        transaction.create(member_ref, {"id": user["id"], "user_id": user["id"], "role": "owner", "status": "active", "created_at": user["created_at"]})
        transaction.create(preferences_ref, {"lead_time_days": 7, "customer_instalments_enabled": True, "supplier_bills_enabled": True})
        try:
            transaction.commit()
        except Exception as exc:
            if email_ref.get().exists:
                raise ValueError("duplicate_email") from exc
            raise

    def ensure_demo_user(self, password_hash: str) -> None:
        if self.get_by_id("user_demo"):
            return
        demo = {
            "id": "user_demo", "email": "demo@dukaanflow.in", "full_name": "Ramesh Kumar (Demo)",
            "password_hash": password_hash, "business_id": "biz_demo_kirana", "business_name": "Demo Kirana Store",
            "role": "owner", "is_active": True, "created_at": "2026-10-17T00:00:00Z",
        }
        if self.db.mode in ("firestore", "emulator"):
            business_ref = self.db.business_document("biz_demo_kirana")
            if not business_ref.get().exists:
                batch = self.db.firestore_client.batch()
                batch.set(business_ref, {**DEFAULT_SEED_DATA["business"], "id": "biz_demo_kirana"})
                for field in ("customers", "suppliers", "supplier_bills", "transactions"):
                    for row in DEFAULT_SEED_DATA[field]:
                        batch.set(self.db.business_collection("biz_demo_kirana", field).document(row["id"]), row)
                batch.set(self.db.business_collection("biz_demo_kirana", "settings").document("notification_preferences"), DEFAULT_SEED_DATA["notification_preferences"])
                batch.commit()
            email_ref = self.db.collection("user_email_index").document(self.email_key(demo["email"]))
            user_ref = self.db.collection("users").document("user_demo")
            member_ref = self.db.business_collection("biz_demo_kirana", "members").document("user_demo")
            tx = self.db.firestore_client.transaction()
            if not user_ref.get().exists:
                tx.set(user_ref, demo)
                tx.set(email_ref, {"user_id": "user_demo", "email": demo["email"]})
                tx.set(member_ref, {"id": "user_demo", "user_id": "user_demo", "role": "owner", "status": "active", "created_at": demo["created_at"]})
                tx.commit()
            return
        users = seed_service._memory_data.setdefault("users", [])
        if not any(u["id"] == "user_demo" for u in users):
            users.append(demo)
        seed_service._memory_data.setdefault("businesses", {}).setdefault("biz_demo_kirana", DEFAULT_SEED_DATA["business"])


user_repo = UserRepository()
