"""Database connectivity and Firestore adapter.

Supports:
1. Google Cloud Firestore (production & staging)
2. Firestore Emulator (local development & integration testing)
3. In-memory fallback (isolated unit tests and zero-dependency mode)
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
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

        if project_id or emulator_host:
            try:
                from google.cloud import firestore
                self._firestore_client = firestore.Client(project=project_id)
                self.mode = "emulator" if emulator_host else "firestore"
            except Exception:
                self.mode = "in_memory"

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
