"""Authentication API routes for DukaanFlow.

Endpoints:
- POST /api/v1/auth/register : Register a new user and create their business tenant.
- POST /api/v1/auth/login    : Authenticate credentials and receive a signed JWT access token.
- GET  /api/v1/auth/me       : Retrieve currently authenticated user profile and business details.
"""
from fastapi import APIRouter, Depends, status

from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserDTO,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services.auth_service import login_user, register_user
from app.core.auth import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest):
    """Register a new merchant account and generate an isolated business workspace."""
    result = register_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        business_name=payload.business_name,
    )
    return result


@router.post("/login", response_model=AuthTokenResponse, status_code=status.HTTP_200_OK)
def login(payload: UserLoginRequest):
    """Authenticate with email and password to receive a Bearer JWT access token."""
    result = login_user(
        email=payload.email,
        password=payload.password,
    )
    return result


@router.get("/me", response_model=AuthUserDTO, status_code=status.HTTP_200_OK)
def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieve identity and tenant information for the authenticated user."""
    return AuthUserDTO(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        business_id=current_user["business_id"],
        business_name=current_user.get("business_name", ""),
        role=current_user.get("role", "owner"),
    )
