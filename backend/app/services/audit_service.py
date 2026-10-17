"""Centralized Financial Audit and Idempotency Service.

Maintains immutable records of all financial events and protects against
duplicate submissions via idempotency keys.
"""
import time
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from app.services.seed_data import seed_service
from app.core.database import get_db
from app.core.database import persist_set
from app.core.tenant_context import get_business_id, get_user_id

# Idempotency cache: (business_id, key) -> (expiry_time, cached_response)
_IDEMPOTENCY_CACHE: Dict[str, tuple[float, Any]] = {}
IDEMPOTENCY_TTL_SECONDS = 300  # 5 minutes


class AuditService:
    def log_event(
        self,
        business_id: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an immutable audit event for a financial or business mutation."""
        event_id = f"audit_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        business_id = get_business_id()
        event = {
            "id": event_id,
            "business_id": business_id,
            "actor_id": get_user_id(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "request_id": request_id or f"req_{uuid.uuid4().hex[:8]}",
            "metadata": metadata or {},
            "created_at": timestamp,
        }

        events = seed_service._data.setdefault("audit_events", [])
        events.append(event)

        return event

    def list_events(
        self,
        business_id: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve chronological audit trail for a business."""
        business_id = get_business_id()
        events = seed_service._data.get("audit_events", [])

        filtered = [
            e for e in events
            if (not entity_type or e.get("entity_type") == entity_type)
        ]
        return sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

    def check_idempotency(self, business_id: str, idempotency_key: Optional[str]) -> Optional[Any]:
        """Check if an operation with this idempotency key was already completed."""
        if not idempotency_key:
            return None

        db = get_db()
        if db.mode in ("firestore", "emulator"):
            doc_id = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
            ref = db.business_collection(get_business_id(), "idempotency").document(doc_id)
            snap = ref.get()
            if not snap.exists:
                return None
            cached = snap.to_dict() or {}
            if cached.get("expires_at", 0) > time.time():
                return cached.get("response")
            ref.delete()
            return None
        cache_key = f"{get_business_id()}:{idempotency_key}"
        cached = _IDEMPOTENCY_CACHE.get(cache_key)
        if cached:
            expires_at, response = cached
            if time.time() < expires_at:
                return response
            else:
                del _IDEMPOTENCY_CACHE[cache_key]
        return None

    def record_idempotency(self, business_id: str, idempotency_key: Optional[str], response_data: Any) -> None:
        """Cache the result of an operation under an idempotency key for 5 minutes."""
        if not idempotency_key:
            return

        db = get_db()
        if db.mode in ("firestore", "emulator"):
            doc_id = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
            persist_set(db.business_collection(get_business_id(), "idempotency").document(doc_id), {
                "id": idempotency_key, "response": response_data, "expires_at": time.time() + IDEMPOTENCY_TTL_SECONDS,
            })
            return
        cache_key = f"{get_business_id()}:{idempotency_key}"
        _IDEMPOTENCY_CACHE[cache_key] = (time.time() + IDEMPOTENCY_TTL_SECONDS, response_data)


audit_service = AuditService()
