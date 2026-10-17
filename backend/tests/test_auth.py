"""Tests for custom JWT authentication, tenant isolation, and security controls.

Uses the `no_auth_override` marker to test the raw authentication pipeline
without the default test fixture override.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_seed_state():
    """Ensure clean seed state before each auth test."""
    seed_service.reset()


@pytest.mark.no_auth_override
def test_unauthenticated_request_returns_401():
    """Unauthenticated access to any protected route must return 401 Unauthorized."""
    # Ensure no dependency overrides are active
    app.dependency_overrides.clear()
    
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 401
    assert "detail" in res.json() or "error" in res.json()


@pytest.mark.no_auth_override
def test_invalid_bearer_token_returns_401():
    """Requests with malformed or fake JWT tokens must return 401."""
    app.dependency_overrides.clear()
    
    res = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": "Bearer invalid.jwt.token.here"},
    )
    assert res.status_code == 401


@pytest.mark.no_auth_override
def test_health_endpoints_remain_unauthenticated():
    """Health probes must always succeed without any auth headers."""
    app.dependency_overrides.clear()
    
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json() == {"status": "alive"}

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


@pytest.mark.no_auth_override
def test_user_registration_success():
    """Valid user registration returns 201, valid JWT token, and user DTO."""
    app.dependency_overrides.clear()
    
    payload = {
        "email": "merchant_unique@example.com",
        "password": "StrongPassword123!",
        "full_name": "Suresh Raina",
        "business_name": "Raina Provision Store",
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert data["user"]["email"] == "merchant_unique@example.com"
    assert data["user"]["full_name"] == "Suresh Raina"
    assert data["user"]["business_id"].startswith("biz_")
    assert data["user"]["business_name"] == "Raina Provision Store"


@pytest.mark.no_auth_override
def test_user_registration_duplicate_email_rejected():
    """Registering with an already-used email must return 409 Conflict."""
    app.dependency_overrides.clear()
    
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "User One",
        "business_name": "Store One",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409


@pytest.mark.no_auth_override
def test_user_registration_validation_errors():
    """Invalid email format or too-short password returns 422 Validation Error."""
    app.dependency_overrides.clear()
    
    # Invalid email
    res1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "ValidPassword123",
            "full_name": "Valid Name",
            "business_name": "Valid Biz",
        },
    )
    assert res1.status_code == 422

    # Password too short (< 8 chars)
    res2 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@example.com",
            "password": "short",
            "full_name": "Valid Name",
            "business_name": "Valid Biz",
        },
    )
    assert res2.status_code == 422


@pytest.mark.no_auth_override
def test_user_login_success():
    """Login with correct credentials returns 200 and access token."""
    app.dependency_overrides.clear()
    
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "SecurePassword999",
            "full_name": "Login User",
            "business_name": "Login Enterprises",
        },
    )

    # Login
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@example.com", "password": "SecurePassword999"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login_test@example.com"


@pytest.mark.no_auth_override
def test_user_login_invalid_password_returns_401():
    """Login with wrong password must return 401 Unauthorized."""
    app.dependency_overrides.clear()
    
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong_pwd@example.com",
            "password": "CorrectPassword123",
            "full_name": "User",
            "business_name": "Biz",
        },
    )

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong_pwd@example.com", "password": "WrongPassword999"},
    )
    assert res.status_code == 401


@pytest.mark.no_auth_override
def test_user_login_nonexistent_email_returns_401():
    """Login with non-existent email must return 401 Unauthorized."""
    app.dependency_overrides.clear()
    
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "AnyPassword123"},
    )
    assert res.status_code == 401


@pytest.mark.no_auth_override
def test_authenticated_me_endpoint():
    """GET /api/v1/auth/me returns identity of authenticated user."""
    app.dependency_overrides.clear()
    
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "me_test@example.com",
            "password": "MySecretPassword123",
            "full_name": "Me Tester",
            "business_name": "Me Store",
        },
    )
    token = reg_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "me_test@example.com"
    assert me_data["full_name"] == "Me Tester"
    assert me_data["business_name"] == "Me Store"


@pytest.mark.no_auth_override
def test_protected_route_with_bearer_token():
    """Protected routes succeed when presented with valid Bearer token."""
    app.dependency_overrides.clear()
    
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "bearer_access@example.com",
            "password": "StrongPassword789!",
            "full_name": "Bearer User",
            "business_name": "Bearer Biz",
        },
    )
    token = reg_res.json()["access_token"]

    dash_res = client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dash_res.status_code == 200


def test_seed_reset_guarded_in_production(monkeypatch):
    """Seed reset endpoint returns 403 Forbidden when ENVIRONMENT is production."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    res = client.post("/api/v1/seed/reset")
    assert res.status_code == 403
    assert "only allowed in development" in res.json().get("error", {}).get("message", "")


@pytest.mark.no_auth_override
def test_tenant_isolation_idor_prevention():
    """Verify that User A cannot access User B's business tenant (cross-tenant IDOR)."""
    app.dependency_overrides.clear()
    from app.core.auth import check_tenant_isolation
    from fastapi import HTTPException

    # Register Tenant A
    res_a = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tenant_a@example.com",
            "password": "PasswordA123!",
            "full_name": "Merchant A",
            "business_name": "Store A",
        },
    )
    biz_a = res_a.json()["user"]["business_id"]

    # Register Tenant B
    res_b = client.post(
        "/api/v1/auth/register",
        json={
            "email": "tenant_b@example.com",
            "password": "PasswordB123!",
            "full_name": "Merchant B",
            "business_name": "Store B",
        },
    )
    biz_b = res_b.json()["user"]["business_id"]

    assert biz_a != biz_b

    # Verify cross-tenant isolation enforcement
    with pytest.raises(HTTPException) as exc_info:
        check_tenant_isolation(requested_business_id=biz_b, user_business_id=biz_a)
    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail
