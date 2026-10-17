"""Authentication and tenant isolation dependencies for FastAPI.

Provides:
- get_current_user: verifies Bearer token, validates expiry, returns user dict.
- get_current_business_id: extracts business_id from authenticated user.
- require_business_access: validates that a requested business matches the user's business.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import decode_access_token, get_user_by_id
from app.core.database import get_db
from app.core.database import RequestWriteBatch, RequestWriteLimitExceeded
from app.core.tenant_context import set_business_id, set_user_id, set_write_batch

# Use HTTPBearer with auto_error=False for cleaner error handling
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> AsyncGenerator[dict, None]:
    """Validate Bearer JWT token and return authenticated user object.

    Raises:
        HTTPException 401 if token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token claims: missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found or account deactivated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    business_id = user.get("business_id")
    if not business_id:
        raise HTTPException(status_code=403, detail="User is not associated with an active business.")
    db = get_db()
    if db.mode in ("firestore", "emulator"):
        member = db.business_collection(business_id, "members").document(user_id).get()
        if not member.exists or (member.to_dict() or {}).get("status") != "active":
            raise HTTPException(status_code=403, detail="Business membership is inactive.")
    context_token = set_business_id(business_id)
    user_token = set_user_id(user_id)
    db = get_db()
    batch = RequestWriteBatch(db.firestore_client) if db.firestore_client else None
    batch_token = set_write_batch(batch)
    try:
        yield user
    except BaseException:
        raise
    else:
        if batch is not None:
            try:
                batch.commit()
            except RequestWriteLimitExceeded as exc:
                raise HTTPException(status_code=413, detail=str(exc)) from exc
    finally:
        from app.core.tenant_context import reset_business_id, reset_user_id, reset_write_batch
        reset_business_id(context_token)
        reset_user_id(user_token)
        reset_write_batch(batch_token)


async def get_current_business_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    """Extract business_id from the authenticated user context.

    Ensures tenant isolation across all endpoints.
    """
    business_id = current_user.get("business_id")
    if not business_id:
        raise HTTPException(
            status_code=403,
            detail="User is not associated with any active business.",
        )
    return business_id


def check_tenant_isolation(requested_business_id: str, user_business_id: str) -> None:
    """Verify that the user belongs to the requested business.

    Raises:
        HTTPException 403 if attempting cross-tenant access.
    """
    if requested_business_id != user_business_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Access to another business's data is denied.",
        )
