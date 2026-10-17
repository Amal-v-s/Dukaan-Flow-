"""Centralized Financial Audit and Idempotency Service.

Maintains immutable records of all financial events and protects against
duplicate submissions via idempotency keys.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException

from app.services.seed_data import seed_service

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

        event = {
            "id": event_id,
            "business_id": business_id,
            "actor_id": actor_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "request_id": request_id or f"req_{uuid.uuid4().hex[:8]}",
            "metadata": metadata or {},
            "created_at": timestamp,
        }

        # Store in seed_service._data for local/dev, or tenant-scoped store
        events = seed_service._data.setdefault("audit_events", [])
        events.append(event)

        # Also store under business_data if tenant exists
        if business_id and business_id != "biz_demo_kirana":
            b_data = seed_service._data.setdefault("business_data", {}).setdefault(business_id, {})
            b_data.setdefault("audit_events", []).append(event)

        return event

    def list_events(
        self,
        business_id: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve chronological audit trail for a business."""
        if business_id and business_id != "biz_demo_kirana":
            b_data = seed_service._data.setdefault("business_data", {}).setdefault(business_id, {})
            events = b_data.get("audit_events", [])
        else:
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

        cache_key = f"{business_id}:{idempotency_key}"
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

        cache_key = f"{business_id}:{idempotency_key}"
        _IDEMPOTENCY_CACHE[cache_key] = (time.time() + IDEMPOTENCY_TTL_SECONDS, response_data)


audit_service = AuditService()
