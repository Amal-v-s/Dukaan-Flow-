"""Pytest configuration and global fixtures.

Provides automatic demo user authentication override for backward-compatible
testing of existing test suites. Tests specifically exercising the auth layer
can use the `no_auth_override` marker to test raw unauthenticated/authenticated
requests against the actual JWT implementation.
"""
import pytest
from app.main import app
from app.core.auth import get_current_user


@pytest.fixture(autouse=True)
def default_auth_context(request):
    """Provide authenticated demo user context for all non-auth test cases."""
    if "no_auth_override" in request.keywords:
        yield
        return

    demo_user = {
        "id": "user_demo",
        "email": "demo@dukaanflow.in",
        "full_name": "Ramesh Kumar (Demo)",
        "business_id": "biz_demo_kirana",
        "role": "owner",
        "is_active": True,
    }
    app.dependency_overrides[get_current_user] = lambda: demo_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_user, None)
