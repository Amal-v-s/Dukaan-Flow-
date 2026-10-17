"""Compatibility persistence layer for the existing service model.

Collections are stored as individual documents beneath each business. The
wrappers preserve the current service-facing list/dict API while persisting
mutations immediately. New feature code should prefer explicit repositories.
"""
from collections.abc import MutableMapping, MutableSequence
from copy import deepcopy
from typing import Any

from app.core.database import DatabaseClient, persist_delete, persist_set, read_document, stream_documents

LIST_COLLECTIONS = {
    "customers": "customers",
    "suppliers": "suppliers",
    "supplier_bills": "supplier_bills",
    "transactions": "cash_events",
    "repayment_plans": "repayment_plans",
    "budgets": "budgets",
    "audit_events": "audit_events",
    "ai_interaction_logs": "ai_interaction_logs",
}
DICT_COLLECTIONS = {"reminders": "reminders", "import_batches": "import_batches", "scenarios": "scenarios"}
_DEFAULT_PREFERENCES = {
    "lead_time_days": 7,
    "customer_instalments_enabled": True,
    "supplier_bills_enabled": True,
}


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return deepcopy(value)


class TrackedDict(dict):
    def __init__(self, value: dict, changed):
        dict.__init__(self, value)
        self._changed = changed

    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, dict) and not isinstance(value, TrackedDict):
            value = TrackedDict(value, lambda _changed: self._changed(_plain(self)))
            dict.__setitem__(self, key, value)
        elif isinstance(value, list) and not isinstance(value, TrackedList):
            value = TrackedList(value, lambda _changed: self._changed(_plain(self)))
            dict.__setitem__(self, key, value)
        return value

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self._changed(_plain(self))

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._changed(_plain(self))

    def update(self, *args, **kwargs):
        dict.update(self, *args, **kwargs)
        self._changed(_plain(self))

    def pop(self, key, *args):
        value = dict.pop(self, key, *args)
        self._changed(_plain(self))
        return value


class TrackedList(list):
    def __init__(self, value: list, changed):
        list.__init__(self, value)
        self._changed = changed

    def __getitem__(self, index):
        value = list.__getitem__(self, index)
        if isinstance(value, dict) and not isinstance(value, TrackedDict):
            value = TrackedDict(value, self._changed)
            list.__setitem__(self, index, value)
        elif isinstance(value, list) and not isinstance(value, TrackedList):
            value = TrackedList(value, self._changed)
            list.__setitem__(self, index, value)
        return value

    def append(self, value):
        list.append(self, value)
        self._changed(_plain(self))

    def extend(self, values):
        list.extend(self, values)
        self._changed(_plain(self))

    def __setitem__(self, index, value):
        list.__setitem__(self, index, value)
        self._changed(_plain(self))

    def __delitem__(self, index):
        list.__delitem__(self, index)
        self._changed(_plain(self))

    def pop(self, index=-1):
        value = list.pop(self, index)
        self._changed(_plain(self))
        return value

    def remove(self, value):
        list.remove(self, value)
        self._changed(_plain(self))


class FirestoreCollectionList(MutableSequence):
    def __init__(self, collection):
        self.collection = collection

    def _refs(self):
        return stream_documents(self.collection)

    def __len__(self):
        return len(self._refs())

    def __getitem__(self, index):
        refs = self._refs()
        if isinstance(index, slice):
            return [self._wrap(s.reference, s.to_dict() or {}) for s in refs[index]]
        snap = refs[index]
        return self._wrap(snap.reference, snap.to_dict() or {})

    @staticmethod
    def _wrap(ref, value):
        return TrackedDict(value, lambda changed: persist_set(ref, changed))

    def __setitem__(self, index, value):
        ref = self._refs()[index].reference
        persist_set(ref, _plain(value))

    def __delitem__(self, index):
        persist_delete(self._refs()[index].reference)

    def insert(self, index, value):
        value = _plain(value)
        doc_id = value.get("id")
        if not doc_id:
            raise ValueError("Firestore records must have an id")
        persist_set(self.collection.document(str(doc_id)), value)

    def append(self, value):
        self.insert(len(self), value)

    def sort(self, *args, **kwargs):
        # Service callers sort only for presentation; persistence order is not semantic.
        values = list(self)
        values.sort(*args, **kwargs)
        self._sorted_cache = values


class FirestoreCollectionDict(MutableMapping):
    def __init__(self, collection):
        self.collection = collection

    def __getitem__(self, key):
        snap = read_document(self.collection.document(str(key)))
        if not snap.exists:
            raise KeyError(key)
        return TrackedDict(snap.to_dict() or {}, lambda changed: persist_set(self.collection.document(str(key)), changed))

    def __setitem__(self, key, value):
        value = _plain(value)
        value.setdefault("id", str(key))
        persist_set(self.collection.document(str(key)), value)

    def __delitem__(self, key):
        ref = self.collection.document(str(key))
        if not read_document(ref).exists:
            raise KeyError(key)
        persist_delete(ref)

    def __iter__(self):
        return (snap.id for snap in stream_documents(self.collection))

    def __len__(self):
        return len(stream_documents(self.collection))

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = {} if default is None else default
            return self[key]


class FirestoreTenantData(MutableMapping):
    def __init__(self, db: DatabaseClient, business_id: str):
        self.db = db
        self.business_id = business_id
        self._business_ref = db.business_document(business_id)

    def __getitem__(self, key):
        if key == "business":
            snap = read_document(self._business_ref)
            if not snap.exists:
                raise KeyError(key)
            return TrackedDict(snap.to_dict() or {}, lambda value: persist_set(self._business_ref, value))
        if key in LIST_COLLECTIONS:
            return FirestoreCollectionList(self.db.business_collection(self.business_id, LIST_COLLECTIONS[key]))
        if key in DICT_COLLECTIONS:
            return FirestoreCollectionDict(self.db.business_collection(self.business_id, DICT_COLLECTIONS[key]))
        if key == "notification_preferences":
            ref = self.db.business_collection(self.business_id, "settings").document("notification_preferences")
            snap = read_document(ref)
            value = snap.to_dict() if snap.exists else _DEFAULT_PREFERENCES.copy()
            return TrackedDict(value or {}, lambda changed: persist_set(ref, changed))
        if key == "businesses":
            return FirestoreCollectionDict(self.db.collection("businesses"))
        if key == "users":
            return FirestoreCollectionList(self.db.collection("users"))
        if key == "business_data":
            return FirestoreCollectionDict(self.db.collection("business_data"))
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key == "business":
            persist_set(self._business_ref, _plain(value))
        elif key in DICT_COLLECTIONS:
            collection = self.db.business_collection(self.business_id, DICT_COLLECTIONS[key])
            for doc in collection.stream():
                persist_delete(doc.reference)
            for doc_id, data in value.items():
                persist_set(collection.document(str(doc_id)), _plain(data))
        elif key == "notification_preferences":
            persist_set(self.db.business_collection(self.business_id, "settings").document("notification_preferences"), _plain(value))
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        raise KeyError("Tenant data collections cannot be removed")

    def __iter__(self):
        return iter((*LIST_COLLECTIONS.keys(), *DICT_COLLECTIONS.keys(), "business", "notification_preferences"))

    def __len__(self):
        return len(LIST_COLLECTIONS) + len(DICT_COLLECTIONS) + 2

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            self[key] = {} if default is None else default
            return self[key]
