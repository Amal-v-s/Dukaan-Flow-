"""Authentication and user management service.

Uses bcrypt for password hashing and PyJWT for stateless access tokens.
User/business data is stored in the in-memory seed service for Phase 4B;
Phase 4D will migrate to Firestore.
"""
import uuid
import time
from datetime import datetime, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException

from app.core.config import settings
from app.services.seed_data import seed_service


# JWT configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600 * 8  # 8 hours


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt with automatic salt generation."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_access_token(user_id: str, email: str, business_id: str, role: str = "owner") -> tuple[str, int]:
    """Create a signed JWT access token. Returns (token, expires_in_seconds)."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "business_id": business_id,
        "role": role,
        "iat": now,
        "exp": now + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_SECONDS


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid authentication token")


def _ensure_demo_user():
    users = seed_service._data.setdefault("users", [])
    if not any(u["email"] == "demo@dukaanflow.in" for u in users):
        users.append({
            "id": "user_demo",
            "email": "demo@dukaanflow.in",
            "full_name": "Ramesh Kumar (Demo)",
            "password_hash": _hash_password("password123"),
            "business_id": "biz_demo_kirana",
            "business_name": "Demo Kirana Store",
            "role": "owner",
            "is_active": True,
            "created_at": "2026-10-17T00:00:00Z",
        })
    businesses = seed_service._data.setdefault("businesses", {})
    if "biz_demo_kirana" not in businesses:
        businesses["biz_demo_kirana"] = seed_service._data.get("business", {
            "id": "biz_demo_kirana",
            "name": "Demo Kirana Store",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "opening_cash_paise": 1500000,
            "cash_safety_buffer_paise": 1500000,
            "is_demo": True,
        })


def register_user(email: str, password: str, full_name: str, business_name: str) -> dict:
    """Register a new user and create their business.

    Returns the auth token response dict.
    """
    _ensure_demo_user()
    users = seed_service._data.setdefault("users", [])

    # Check for duplicate email
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Create business
    business_id = f"biz_{uuid.uuid4().hex[:12]}"
    businesses = seed_service._data.setdefault("businesses", {})
    businesses[business_id] = {
        "id": business_id,
        "name": business_name,
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "opening_cash_paise": 0,
        "cash_safety_buffer_paise": 1500000,  # ₹15,000 default
        "is_demo": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Create user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "password_hash": _hash_password(password),
        "business_id": business_id,
        "business_name": business_name,
        "role": "owner",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)

    # Initialize business data collections
    seed_service._data.setdefault("business_data", {})[business_id] = {
        "customers": [],
        "suppliers": [],
        "supplier_bills": [],
        "transactions": [],
        "repayment_plans": [],
        "budgets": [],
        "reminders": {},
        "audit_events": [],
        "ai_interaction_logs": [],
        "import_batches": {},
        "notification_preferences": {
            "lead_time_days": 7,
            "customer_instalments_enabled": True,
            "supplier_bills_enabled": True,
        },
    }

    # Generate token
    token, expires_in = _create_access_token(user_id, email, business_id, "owner")

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "business_id": business_id,
            "business_name": business_name,
            "role": "owner",
        },
    }


def login_user(email: str, password: str) -> dict:
    """Authenticate a user and return an access token.

    Returns the auth token response dict.
    """
    users = seed_service._data.get("users", [])
    user = next((u for u in users if u["email"] == email and u["is_active"]), None)

    if not user or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    business_id = user["business_id"]
    businesses = seed_service._data.get("businesses", {})
    business = businesses.get(business_id, {})

    token, expires_in = _create_access_token(
        user["id"], user["email"], business_id, user.get("role", "owner")
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "business_id": business_id,
            "business_name": business.get("name", ""),
            "role": user.get("role", "owner"),
        },
    }


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Look up a user by ID. Returns None if not found."""
    users = seed_service._data.get("users", [])
    return next((u for u in users if u["id"] == user_id and u["is_active"]), None)
