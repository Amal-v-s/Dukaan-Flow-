"""Firestore connection and tenant-scoped persistence helpers.

The in-memory implementation remains available when no Firestore project is
configured (local tests/demo). Configured Firestore connections fail closed;
they never silently fall back to volatile storage.
"""
import os
from typing import Any, Dict, List, Optional
from app.core.config import settings

_db_instance = None


class InMemoryCollection:
    """Mock Firestore collection adapter for local fallback."""
    def __init__(self, name: str, data_store: Dict[str, Any]):
        self.name = name
        self.store = data_store

    def document(self, doc_id: str):
        return InMemoryDocument(self.name, doc_id, self.store)

    def get(self) -> List["InMemoryDocumentSnapshot"]:
        coll_data = self.store.setdefault(self.name, {})
        return [InMemoryDocumentSnapshot(k, v) for k, v in coll_data.items()]


class InMemoryDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]]):
        self.id = doc_id
        self._data = data
        self.exists = data is not None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return self._data.copy() if self._data else None


class InMemoryDocument:
    def __init__(self, coll_name: str, doc_id: str, data_store: Dict[str, Any]):
        self.coll_name = coll_name
        self.doc_id = doc_id
        self.store = data_store

    def get(self) -> InMemoryDocumentSnapshot:
        coll = self.store.get(self.coll_name, {})
        doc = coll.get(self.doc_id)
        return InMemoryDocumentSnapshot(self.doc_id, doc)

    def set(self, data: Dict[str, Any], merge: bool = False):
        coll = self.store.setdefault(self.coll_name, {})
        if merge and self.doc_id in coll:
            coll[self.doc_id].update(data)
        else:
            coll[self.doc_id] = data

    def update(self, data: Dict[str, Any]):
        coll = self.store.setdefault(self.coll_name, {})
        if self.doc_id in coll:
            coll[self.doc_id].update(data)
        else:
            coll[self.doc_id] = data

    def delete(self):
        coll = self.store.get(self.coll_name, {})
        coll.pop(self.doc_id, None)


class DatabaseClient:
    def __init__(self):
        self._firestore_client = None
        self._in_memory_store: Dict[str, Any] = {}
        self.mode = "in_memory"

        # Check for Firestore availability
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GCP_PROJECT")
        emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

        if project_id or emulator_host:
            try:
                from google.cloud import firestore
                self._firestore_client = firestore.Client(
                    project=project_id or "dukaanflow-emulator",
                    database=settings.FIRESTORE_DATABASE_ID or "(default)",
                )
                self.mode = "emulator" if emulator_host else "firestore"
            except Exception as exc:
                raise RuntimeError(
                    "Firestore is configured but could not be initialized. "
                    "Install google-cloud-firestore and configure Application Default Credentials."
                ) from exc

    def collection(self, name: str):
        if self._firestore_client:
            return self._firestore_client.collection(name)
        return InMemoryCollection(name, self._in_memory_store)

    def business_collection(self, business_id: str, subcollection_name: str):
        """Scattered subcollection under a specific business document."""
        if self._firestore_client:
            return (
                self._firestore_client.collection("businesses")
                .document(business_id)
                .collection(subcollection_name)
            )
        prefix = f"biz_{business_id}_{subcollection_name}"
        return InMemoryCollection(prefix, self._in_memory_store)

    def business_document(self, business_id: str):
        return self.collection("businesses").document(business_id)

    def business_records(self, business_id: str, collection_name: str):
        return self.business_collection(business_id, collection_name)

    @property
    def firestore_client(self):
        return self._firestore_client

    def check_health(self) -> Dict[str, Any]:
        """Verify storage health and connectivity."""
        if self._firestore_client:
            try:
                # Ping test
                self._firestore_client.collection("_health_probe").document("probe").get()
                return {"status": "healthy", "mode": self.mode, "connected": True}
            except Exception as e:
                return {"status": "degraded", "mode": self.mode, "error": str(e), "connected": False}
        return {"status": "healthy", "mode": "in_memory", "connected": True}


def get_db() -> DatabaseClient:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseClient()
    return _db_instance


def reset_db_for_tests() -> None:
    """Reset the cached adapter, primarily for isolated persistence tests."""
    global _db_instance
    _db_instance = None


def firestore_batch(db: DatabaseClient):
    if db.firestore_client:
        return db.firestore_client.batch()
    return None


def persist_set(ref, data: dict) -> None:
    from app.core.tenant_context import get_write_batch
    batch = get_write_batch()
    if batch is not None:
        batch.set(ref, data)
    else:
        ref.set(data)


def persist_delete(ref) -> None:
    from app.core.tenant_context import get_write_batch
    batch = get_write_batch()
    if batch is not None:
        batch.delete(ref)
    else:
        ref.delete()


class RequestWriteLimitExceeded(Exception):
    pass


class OverlaySnapshot:
    def __init__(self, ref, data):
        self.reference = ref
        self.id = ref.id
        self.exists = data is not None
        self._data = data

    def to_dict(self):
        return self._data.copy() if self._data is not None else None


class RequestWriteBatch:
    """Coalesce request writes by document and expose read-your-writes semantics."""
    MAX_WRITES = 450

    def __init__(self, client):
        self.client = client
        self.writes = {}

    def set(self, ref, data):
        self.writes[ref.path] = (ref, dict(data))

    def delete(self, ref):
        self.writes[ref.path] = (ref, None)

    def read(self, ref):
        pending = self.writes.get(ref.path)
        if pending is not None:
            return OverlaySnapshot(ref, pending[1])
        return ref.get()

    def stream(self, collection):
        docs = {snap.id: snap for snap in collection.stream()}
        prefix = f"{collection.path}/"
        for path, (ref, data) in self.writes.items():
            if not path.startswith(prefix) or path.count("/") != collection.path.count("/") + 1:
                continue
            if data is None:
                docs.pop(ref.id, None)
            else:
                docs[ref.id] = OverlaySnapshot(ref, data)
        return list(docs.values())

    def commit(self):
        if not self.writes:
            return
        if len(self.writes) > self.MAX_WRITES:
            raise RequestWriteLimitExceeded(
                f"This request would write {len(self.writes)} Firestore documents; the safe limit is {self.MAX_WRITES}."
            )
        batch = self.client.batch()
        for ref, data in self.writes.values():
            if data is None:
                batch.delete(ref)
            else:
                batch.set(ref, data)
        batch.commit()


def read_document(ref):
    from app.core.tenant_context import get_write_batch
    batch = get_write_batch()
    return batch.read(ref) if batch is not None else ref.get()


def stream_documents(collection):
    from app.core.tenant_context import get_write_batch
    batch = get_write_batch()
    return batch.stream(collection) if batch is not None else list(collection.stream())
