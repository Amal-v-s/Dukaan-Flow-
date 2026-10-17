"""JWT authentication with persistent Firestore-backed account records."""
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException

from app.core.config import settings
from app.core.database import get_db
from app.repositories.user_repo import user_repo
from app.services.seed_data import seed_service

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600 * 8


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_access_token(user_id: str, email: str, business_id: str, role: str = "owner") -> tuple[str, int]:
    now = int(time.time())
    token = jwt.encode({"sub": user_id, "email": email, "business_id": business_id, "role": role,
                        "iat": now, "exp": now + ACCESS_TOKEN_EXPIRE_SECONDS},
                       settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_SECONDS


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc


def _ensure_demo_user():
    existing = user_repo.get_by_id("user_demo")
    user_repo.ensure_demo_user(existing["password_hash"] if existing else _hash_password("password123"))


def register_user(email: str, password: str, full_name: str, business_name: str) -> dict:
    _ensure_demo_user()
    normalized_email = email.strip().lower()
    if user_repo.get_by_email(normalized_email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    business_id = f"biz_{uuid.uuid4().hex[:12]}"
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    business = {"id": business_id, "name": business_name, "currency": "INR", "timezone": "Asia/Kolkata",
                "opening_cash_paise": 0, "cash_safety_buffer_paise": 1500000, "is_demo": False,
                "created_at": created_at}
    user = {"id": user_id, "email": normalized_email, "full_name": full_name,
            "password_hash": _hash_password(password), "business_id": business_id,
            "business_name": business_name, "role": "owner", "is_active": True,
            "created_at": created_at}
    try:
        user_repo.create_account(user, business)
    except ValueError as exc:
        if str(exc) == "duplicate_email":
            raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
        raise

    token, expires_in = _create_access_token(user_id, normalized_email, business_id, "owner")
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in,
            "user": {"id": user_id, "email": normalized_email, "full_name": full_name,
                     "business_id": business_id, "business_name": business_name, "role": "owner"}}


def login_user(email: str, password: str) -> dict:
    _ensure_demo_user()
    user = user_repo.get_by_email(email.strip().lower())
    if not user or not user.get("is_active") or not _verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    business_id = user["business_id"]
    if user_repo.db.mode in ("firestore", "emulator"):
        snap = user_repo.db.business_document(business_id).get()
        business = snap.to_dict() if snap.exists else {}
    else:
        business = seed_service._memory_data.get("businesses", {}).get(business_id, {})
    token, expires_in = _create_access_token(user["id"], user["email"], business_id, user.get("role", "owner"))
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in,
            "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"],
                     "business_id": business_id, "business_name": business.get("name", ""),
                     "role": user.get("role", "owner")}}


def get_user_by_id(user_id: str) -> Optional[dict]:
    user = user_repo.get_by_id(user_id)
    return user if user and user.get("is_active") else None
