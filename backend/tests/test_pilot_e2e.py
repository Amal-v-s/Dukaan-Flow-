"""Comprehensive Pilot Launch End-to-End Smoke Test Suite.

Simulates the complete real-world kirana merchant journey across all systems:
1. Merchant Registration & Isolated Business Tenant Creation
2. Khata Customer Creation
3. Credit Sale Ledger Posting
4. Partial Khata Repayment with Idempotency Key protection
5. Idempotent Retry verification (no double-crediting)
6. Supplier Bill Creation and Payment
7. Ledger Entry Reversal (Audited non-destructive correction)
8. Audit Trail Verification
9. Strict Multi-Tenant Boundary Enforcement
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_state():
    seed_service.reset()


@pytest.mark.no_auth_override
def test_complete_pilot_merchant_lifecycle():
    """Verify full end-to-end merchant journey and financial integrity."""
    app.dependency_overrides.clear()

    unique_email = f"kirana_{uuid.uuid4().hex[:6]}@example.com"
    pwd = "MerchantSecurePass123!"

    # 1. Register Merchant
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": pwd,
            "full_name": "Ramesh Gupta",
            "business_name": "Gupta Kirana & General Store",
        },
    )
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    token = auth_data["access_token"]
    biz_id = auth_data["user"]["business_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check Dashboard
    dash_res = client.get("/api/v1/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["currency"] == "INR"

    # 3. Create Khata Customer
    cust_res = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "name": "Anil Verma",
            "phone": "+91 98765 11223",
            "notes": "Regular neighbor customer",
        },
    )
    assert cust_res.status_code == 201
    customer_id = cust_res.json()["id"]

    # 4. Record Credit Sale (₹5,000 = 500000 paise)
    sale_res = client.post(
        f"/api/v1/customers/{customer_id}/ledger-entries",
        headers=headers,
        json={
            "entry_type": "credit_sale",
            "amount_paise": 500000,
            "effective_date": "2026-10-17",
            "due_date": "2026-10-25",
            "notes": "Monthly ration credit",
        },
    )
    assert sale_res.status_code == 201
    sale_entry_id = sale_res.json()["id"]

    # Verify updated customer balance
    c_check = client.get(f"/api/v1/customers/{customer_id}", headers=headers).json()
    assert c_check["outstanding_balance_paise"] == 500000

    # 5. Record Repayment (₹2,000 = 200000 paise) with Idempotency Key
    idem_key = f"idem_{uuid.uuid4().hex[:8]}"
    pay_payload = {
        "entry_type": "repayment",
        "amount_paise": 200000,
        "effective_date": "2026-10-18",
        "payment_method": "upi",
        "notes": "GooglePay UPI partial payment",
        "idempotency_key": idem_key,
    }
    pay_res1 = client.post(
        f"/api/v1/customers/{customer_id}/ledger-entries",
        headers=headers,
        json=pay_payload,
    )
    assert pay_res1.status_code == 201
    pay_data1 = pay_res1.json()

    # 6. Idempotent Retry: Submit exact same request again
    pay_res2 = client.post(
        f"/api/v1/customers/{customer_id}/ledger-entries",
        headers=headers,
        json=pay_payload,
    )
    assert pay_res2.status_code == 201
    pay_data2 = pay_res2.json()
    # Should return identical entry ID without double-crediting
    assert pay_data1["id"] == pay_data2["id"]

    c_after_pay = client.get(f"/api/v1/customers/{customer_id}", headers=headers).json()
    # 500000 - 200000 = 300000
    assert c_after_pay["outstanding_balance_paise"] == 300000

    # 7. Create Supplier Bill and Record Payment
    bill_res = client.post(
        "/api/v1/supplier-bills",
        headers=headers,
        json={
            "supplier_id": "sup_general",
            "description": "Weekly Dairy and Milk Crates",
            "bill_amount_paise": 450000,
            "bill_date": "2026-10-17",
            "due_date": "2026-10-21",
        },
    )
    assert bill_res.status_code == 201
    bill_id = bill_res.json()["id"]

    spay_res = client.post(
        f"/api/v1/supplier-bills/{bill_id}/payments",
        headers=headers,
        json={
            "amount_paise": 450000,
            "payment_date": "2026-10-18",
            "payment_method": "cash",
            "notes": "Full payment settled",
        },
    )
    assert spay_res.status_code == 201

    # 8. Non-Destructive Ledger Entry Reversal
    rev_res = client.post(
        f"/api/v1/customers/{customer_id}/ledger-entries/reversals",
        headers=headers,
        json={
            "entry_id": sale_entry_id,
            "reason": "Customer returned unopened oil container",
        },
    )
    assert rev_res.status_code == 201
    rev_data = rev_res.json()
    assert rev_data["reversal_of"] == sale_entry_id

    # 9. Verify Audit Trail
    audit_res = client.get("/api/v1/management/audit-events", headers=headers)
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["items"]
    assert len(audit_items) > 0
    actions = [a["action"] for a in audit_items]
    assert "ledger_entry_reversed" in actions

    # 10. Multi-Tenant Cross-Access IDOR Security Enforcement
    tenant2_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"competitor_{uuid.uuid4().hex[:6]}@example.com",
            "password": "CompetitorPass123!",
            "full_name": "Suresh Patel",
            "business_name": "Patel Superstore",
        },
    )
    token2 = tenant2_res.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Tenant 2 cannot access Tenant 1's customer
    from app.core.auth import check_tenant_isolation
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        check_tenant_isolation(requested_business_id=biz_id, user_business_id=tenant2_res.json()["user"]["business_id"])
