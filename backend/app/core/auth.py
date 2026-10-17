"""Authentication and tenant isolation dependencies for FastAPI.

Provides:
- get_current_user: verifies Bearer token, validates expiry, returns user dict.
- get_current_business_id: extracts business_id from authenticated user.
- require_business_access: validates that a requested business matches the user's business.
"""
from typing import Optional
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_service import decode_access_token, get_user_by_id

# Use HTTPBearer with auto_error=False for cleaner error handling
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> dict:
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

    return user


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
