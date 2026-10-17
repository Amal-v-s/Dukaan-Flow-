"""Persistence adapter tests that do not require cloud credentials or a running emulator."""
import asyncio
import importlib.util
import os
import uuid
from fastapi.security import HTTPAuthorizationCredentials
from app.core.auth import get_current_user
import pytest
from app.core.tenant_data import FirestoreTenantData
from app.core.tenant_context import reset_business_id, reset_write_batch, set_business_id, set_write_batch
from app.core.database import RequestWriteBatch
from app.services.auth_service import login_user, register_user
from app.repositories.user_repo import UserRepository
from app.services.seed_data import seed_service


class Snapshot:
    def __init__(self, ref):
        self.reference = ref
        self.id = ref.id
        self.exists = ref.data is not None

    def to_dict(self):
        return dict(self.reference.data or {})


class Document:
    def __init__(self, collection, doc_id):
        self.collection = collection
        self.id = str(doc_id)
        self.path = f"{collection.path}/{self.id}"
        self.data = collection.rows.get(self.id)

    def get(self, **_kwargs):
        self.data = self.collection.rows.get(self.id)
        return Snapshot(self)

    def set(self, data, **_kwargs):
        self.collection.rows[self.id] = dict(data)
        self.data = self.collection.rows[self.id]

    def update(self, data):
        self.collection.rows.setdefault(self.id, {}).update(data)
        self.data = self.collection.rows[self.id]

    def delete(self):
        self.collection.rows.pop(self.id, None)


class Collection:
    def __init__(self, path=""):
        self.path = path
        self.rows = {}

    def document(self, doc_id):
        return Document(self, doc_id)

    def stream(self):
        return [Snapshot(Document(self, key)) for key in list(self.rows)]


class FakeFirestore:
    mode = "firestore"
    firestore_client = object()

    def __init__(self):
        self.collections = {}

    def collection(self, name):
        return self.collections.setdefault(name, Collection(name))

    def business_document(self, business_id):
        return self.collection("businesses").document(business_id)

    def business_collection(self, business_id, name):
        return self.collection(f"businesses/{business_id}/{name}")


class FakeWriteBatch:
    def __init__(self, db):
        self.db = db
        self.writes = []

    def set(self, ref, data):
        self.writes.append((ref, data))

    def delete(self, ref):
        self.writes.append((ref, None))

    def commit(self):
        for ref, data in self.writes:
            if data is None:
                ref.delete()
            else:
                ref.set(data)


class FakeFirestoreClient:
    def __init__(self, db):
        self.db = db

    def batch(self):
        return FakeWriteBatch(self.db)

    def transaction(self):
        return FakeTransaction()


class FakeTransaction:
    def __init__(self):
        self.writes = []

    def create(self, ref, data):
        self.writes.append((ref, data))

    def set(self, ref, data):
        self.writes.append((ref, data))

    def commit(self):
        if any(ref.get().exists for ref, _ in self.writes):
            raise ValueError("document exists")
        for ref, data in self.writes:
            ref.set(data)


def test_business_collections_are_tenant_scoped():
    db = FakeFirestore()
    tenant_a = FirestoreTenantData(db, "biz_a")
    tenant_b = FirestoreTenantData(db, "biz_b")
    tenant_a["customers"].append({"id": "cust_1", "name": "A shop"})
    assert [row["id"] for row in tenant_a["customers"]] == ["cust_1"]
    assert list(tenant_b["customers"]) == []


def test_nested_record_mutations_persist_to_the_same_document():
    db = FakeFirestore()
    tenant = FirestoreTenantData(db, "biz_a")
    tenant["customers"].append({"id": "cust_1", "credit_entries": []})
    customer = tenant["customers"][0]
    customer["credit_entries"].append({"id": "entry_1", "amount_paise": 1250})
    customer["name"] = "Updated shop"

    stored = db.business_collection("biz_a", "customers").document("cust_1").get().to_dict()
    assert stored["name"] == "Updated shop"
    assert stored["credit_entries"] == [{"id": "entry_1", "amount_paise": 1250}]


def test_dictionary_records_and_updates_persist():
    db = FakeFirestore()
    tenant = FirestoreTenantData(db, "biz_a")
    batch = tenant["import_batches"].setdefault("batch_1", {"id": "batch_1", "status": "preview"})
    batch["status"] = "completed"
    assert tenant["import_batches"]["batch_1"]["status"] == "completed"


def test_business_document_updates_are_tenant_scoped():
    db = FakeFirestore()
    db.business_document("biz_a").set({"id": "biz_a", "opening_cash_paise": 1000})
    db.business_document("biz_b").set({"id": "biz_b", "opening_cash_paise": 20})
    tenant_a = FirestoreTenantData(db, "biz_a")
    tenant_a["business"]["opening_cash_paise"] += 100
    assert db.business_document("biz_a").get().to_dict()["opening_cash_paise"] == 1100
    assert db.business_document("biz_b").get().to_dict()["opening_cash_paise"] == 20


def test_firestore_account_creation_persists_user_business_membership_and_email_index():
    db = FakeFirestore()
    db.firestore_client = FakeFirestoreClient(db)
    repo = UserRepository()
    repo.db = db
    user = {"id": "user_1", "email": "merchant@example.com", "password_hash": "hash", "is_active": True, "created_at": "2026-10-17T00:00:00Z"}
    business = {"id": "biz_1", "name": "Store"}
    repo.create_account(user, business)

    assert repo.get_by_email("MERCHANT@example.com")["id"] == "user_1"
    assert db.business_collection("biz_1", "members").document("user_1").get().exists
    assert db.business_collection("biz_1", "settings").document("notification_preferences").get().exists
    try:
        repo.create_account({**user, "id": "user_2"}, {**business, "id": "biz_2"})
    except ValueError as exc:
        assert str(exc) == "duplicate_email"
    else:
        raise AssertionError("duplicate email should be rejected")


def _firestore_sdk_available():
    try:
        return importlib.util.find_spec("google.cloud.firestore") is not None
    except ModuleNotFoundError:
        return False


@pytest.mark.firestore_emulator
@pytest.mark.skipif(
    not os.getenv("FIRESTORE_EMULATOR_HOST") or not _firestore_sdk_available(),
    reason="requires google-cloud-firestore and FIRESTORE_EMULATOR_HOST",
)
def test_firestore_emulator_round_trip_is_tenant_scoped():
    from app.core.database import DatabaseClient
    from app.core.tenant_data import FirestoreTenantData

    business_id = f"test_{uuid.uuid4().hex}"
    db = DatabaseClient()
    tenant = FirestoreTenantData(db, business_id)
    tenant["customers"].append({"id": "test_customer", "name": "Emulator customer"})
    assert tenant["customers"][0]["name"] == "Emulator customer"
    try:
        assert list(FirestoreTenantData(db, f"{business_id}_other")["customers"]) == []
    finally:
        db.business_collection(business_id, "customers").document("test_customer").delete()


def test_local_fallback_keeps_registered_businesses_isolated():
    seed_service.reset()
    registered = register_user("isolated@example.com", "Password123!", "Merchant", "Private Store")
    business_id = registered["user"]["business_id"]
    assert login_user("ISOLATED@example.com", "Password123!")["user"]["business_id"] == business_id
    token = set_business_id(business_id)
    try:
        assert seed_service.get_business()["name"] == "Private Store"
        assert seed_service.get_customers() == []
        seed_service.get_customers().append({"id": "private_customer", "name": "Private"})
    finally:
        reset_business_id(token)
    assert [c["id"] for c in seed_service.get_customers()] != ["private_customer"]


def test_verified_jwt_sets_and_cleans_request_tenant_context():
    seed_service.reset()
    registered = register_user("context@example.com", "Password123!", "Context User", "Context Store")
    token = registered["access_token"]
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    dependency = get_current_user(credentials)

    async def exercise():
        user = await anext(dependency)
        assert user["business_id"] == registered["user"]["business_id"]
        from app.core.tenant_context import get_business_id
        assert get_business_id() == registered["user"]["business_id"]
        try:
            await anext(dependency)
        except StopAsyncIteration:
            pass
        assert get_business_id() == "biz_demo_kirana"

    asyncio.run(exercise())


def test_request_batch_coalesces_writes_and_reads_staged_documents():
    db = FakeFirestore()
    batch = RequestWriteBatch(FakeFirestoreClient(db))
    token = set_write_batch(batch)
    try:
        tenant = FirestoreTenantData(db, "biz_a")
        tenant["business"] = {"id": "biz_a", "opening_cash_paise": 1000}
        tenant["business"]["opening_cash_paise"] -= 100
        tenant["business"]["opening_cash_paise"] -= 200
        assert tenant["business"]["opening_cash_paise"] == 700
        assert len(batch.writes) == 1
        assert not db.business_document("biz_a").get().exists
        batch.commit()
    finally:
        reset_write_batch(token)
    assert db.business_document("biz_a").get().to_dict()["opening_cash_paise"] == 700
