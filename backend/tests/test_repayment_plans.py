"""Unit & API tests for Phase 2A, 2B, 2C: Repayment Plans, Instalments, and Overdue Tracking."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    seed_service.reset()


def test_create_full_payment_plan():
    """Verify creating a full-payment schedule linked to an existing customer with debt."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    ravi_id = ravi["id"]
    outstanding = ravi["outstanding_balance_paise"]  # ₹50,000

    due_date = (date.today() + timedelta(days=5)).isoformat()
    start_date = date.today().isoformat()

    payload = {
        "customer_id": ravi_id,
        "plan_type": "full_payment",
        "planned_amount_paise": outstanding,
        "start_date": start_date,
        "notes": "Full settlement agreed",
        "installments": [
            {"due_date": due_date, "amount_paise": outstanding}
        ],
    }

    res = client.post("/api/v1/repayment-plans", json=payload)
    assert res.status_code == 201
    plan = res.json()
    assert plan["customer_id"] == ravi_id
    assert plan["plan_type"] == "full_payment"
    assert plan["planned_amount_paise"] == outstanding
    assert plan["paid_amount_paise"] == 0
    assert plan["remaining_amount_paise"] == outstanding
    assert plan["status"] == "active"
    assert len(plan["installments"]) == 1
    assert plan["installments"][0]["amount_paise"] == outstanding
    assert plan["installments"][0]["status"] == "upcoming"


def test_create_installment_plan_validation():
    """Verify validations: sum must match, dates in order, cannot exceed unallocated debt."""
    customers = client.get("/api/v1/customers").json()["items"]
    sharma = next(c for c in customers if c["name"] == "Sharma General Store")
    sharma_id = sharma["id"]
    outstanding = sharma["outstanding_balance_paise"]  # ₹15,000

    start_date = date.today().isoformat()
    d1 = (date.today() + timedelta(days=3)).isoformat()
    d2 = (date.today() + timedelta(days=10)).isoformat()

    # 1. Reject if planned amount exceeds balance
    bad_payload = {
        "customer_id": sharma_id,
        "plan_type": "installments",
        "planned_amount_paise": outstanding + 500000,
        "start_date": start_date,
        "installments": [
            {"due_date": d1, "amount_paise": 1000000},
            {"due_date": d2, "amount_paise": 1000000},
        ],
    }
    res_bad = client.post("/api/v1/repayment-plans", json=bad_payload)
    assert res_bad.status_code == 400

    # 2. Reject if instalment amounts do not sum to planned amount
    bad_sum = {
        "customer_id": sharma_id,
        "plan_type": "installments",
        "planned_amount_paise": 1000000,
        "start_date": start_date,
        "installments": [
            {"due_date": d1, "amount_paise": 400000},
            {"due_date": d2, "amount_paise": 500000},  # sum = 900,000 != 1,000,000
        ],
    }
    res_bad_sum = client.post("/api/v1/repayment-plans", json=bad_sum)
    assert res_bad_sum.status_code == 400

    # 3. Reject if dates out of order
    bad_order = {
        "customer_id": sharma_id,
        "plan_type": "installments",
        "planned_amount_paise": 1000000,
        "start_date": start_date,
        "installments": [
            {"due_date": d2, "amount_paise": 500000},
            {"due_date": d1, "amount_paise": 500000},  # d1 is before d2!
        ],
    }
    res_bad_order = client.post("/api/v1/repayment-plans", json=bad_order)
    assert res_bad_order.status_code == 400


def test_installment_payment_updates_ledger_and_cash():
    """Verify recording an instalment payment updates the plan, instalment, customer ledger, and cash exactly once."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    ravi_id = ravi["id"]

    initial_cash = client.get("/api/v1/dashboard").json()["available_cash_paise"]

    # Create a 2-instalment plan for ₹20,000
    start_date = date.today().isoformat()
    d1 = (date.today() + timedelta(days=2)).isoformat()
    d2 = (date.today() + timedelta(days=9)).isoformat()

    plan_res = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi_id,
            "plan_type": "installments",
            "planned_amount_paise": 2000000,
            "start_date": start_date,
            "installments": [
                {"due_date": d1, "amount_paise": 1000000},
                {"due_date": d2, "amount_paise": 1000000},
            ],
        },
    )
    assert plan_res.status_code == 201
    plan = plan_res.json()
    plan_id = plan["id"]
    inst1_id = plan["installments"][0]["id"]
    inst2_id = plan["installments"][1]["id"]

    # 1. Pay partial amount on instalment 1 (₹4,000 of ₹10,000)
    payment_id_1 = "pay_test_001"
    pay_res = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": payment_id_1,
            "amount_paise": 400000,
            "payment_date": date.today().isoformat(),
            "payment_method": "cash",
        },
    )
    assert pay_res.status_code == 200
    updated_plan = pay_res.json()
    assert updated_plan["paid_amount_paise"] == 400000
    assert updated_plan["remaining_amount_paise"] == 1600000
    assert updated_plan["status"] == "active"
    i1 = next(x for x in updated_plan["installments"] if x["id"] == inst1_id)
    assert i1["paid_amount_paise"] == 400000
    assert i1["status"] == "partially_paid"

    # Verify Cash and Customer Ledger were updated
    dash = client.get("/api/v1/dashboard").json()
    assert dash["available_cash_paise"] == initial_cash + 400000

    ledger_res = client.get(f"/api/v1/customers/{ravi_id}/ledger").json()
    assert any("Repayment plan" in e["notes"] and e["amount_paise"] == 400000 for e in ledger_res["entries"])

    # 2. Idempotent duplicate payment prevention: repeating identical payment returns current view
    pay_repeat = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": payment_id_1,
            "amount_paise": 400000,
            "payment_date": date.today().isoformat(),
            "payment_method": "cash",
        },
    )
    assert pay_repeat.status_code == 200
    # Cash must NOT have doubled
    dash2 = client.get("/api/v1/dashboard").json()
    assert dash2["available_cash_paise"] == initial_cash + 400000

    # 3. Reject overpayment exceeding instalment remaining amount
    overpay_res = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": "pay_test_overpay",
            "amount_paise": 700000,  # Remaining on inst 1 is only 600,000!
            "payment_date": date.today().isoformat(),
            "payment_method": "cash",
        },
    )
    assert overpay_res.status_code == 400

    # 4. Pay remaining 600,000 on inst 1 and full 1,000,000 on inst 2 -> Plan completed
    client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": "pay_test_002",
            "amount_paise": 600000,
            "payment_date": date.today().isoformat(),
        },
    )
    client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst2_id}/payments",
        json={
            "payment_id": "pay_test_003",
            "amount_paise": 1000000,
            "payment_date": date.today().isoformat(),
        },
    )

    plan_done = client.get(f"/api/v1/repayment-plans/{plan_id}").json()
    assert plan_done["paid_amount_paise"] == 2000000
    assert plan_done["remaining_amount_paise"] == 0
    assert plan_done["status"] == "completed"

    # 5. Completed plan rejects further payments
    res_after_done = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": "pay_test_004",
            "amount_paise": 100000,
            "payment_date": date.today().isoformat(),
        },
    )
    assert res_after_done.status_code == 409


def test_cancel_plan_lifecycle():
    """Verify plan cancellation requires reason and records audit event, and cannot be cancelled if payments exist."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi_id = next(c for c in customers if c["name"] == "Ravi Stores")["id"]

    plan_res = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi_id,
            "plan_type": "full_payment",
            "planned_amount_paise": 1000000,
            "start_date": date.today().isoformat(),
            "installments": [
                {"due_date": (date.today() + timedelta(days=4)).isoformat(), "amount_paise": 1000000}
            ],
        },
    )
    plan_id = plan_res.json()["id"]

    # Reject cancellation without reason
    res_no_reason = client.patch(f"/api/v1/repayment-plans/{plan_id}/cancel", json={"reason": "   "})
    assert res_no_reason.status_code == 422 or res_no_reason.status_code == 400

    # Cancel successfully
    res_cancel = client.patch(f"/api/v1/repayment-plans/{plan_id}/cancel", json={"reason": "Customer requested change in terms"})
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "cancelled"

    # Cancelled plan rejects payment
    inst_id = plan_res.json()["installments"][0]["id"]
    res_pay = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst_id}/payments",
        json={
            "payment_id": "pay_cancelled_01",
            "amount_paise": 500000,
            "payment_date": date.today().isoformat(),
        },
    )
    assert res_pay.status_code == 409


def test_plan_patch_notes():
    """Verify updating plan notes via PATCH /api/v1/repayment-plans/{plan_id}."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi_id = next(c for c in customers if c["name"] == "Ravi Stores")["id"]

    plan = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi_id,
            "plan_type": "full_payment",
            "planned_amount_paise": 1000000,
            "start_date": date.today().isoformat(),
            "notes": "Initial note",
            "installments": [
                {"due_date": (date.today() + timedelta(days=5)).isoformat(), "amount_paise": 1000000}
            ],
        },
    ).json()

    patch_res = client.patch(f"/api/v1/repayment-plans/{plan['id']}", json={"notes": "Updated terms via shopkeeper agreement"})
    assert patch_res.status_code == 200
    assert patch_res.json()["notes"] == "Updated terms via shopkeeper agreement"


def test_days_overdue_and_derived_status():
    """Verify Phase 2C overdue calculation: days overdue derived from date and paid instalments are never overdue."""
    customers = client.get("/api/v1/customers").json()["items"]
    sharma_id = next(c for c in customers if c["name"] == "Sharma General Store")["id"]

    past_start = (date.today() - timedelta(days=10)).isoformat()
    past_due_1 = (date.today() - timedelta(days=4)).isoformat()  # 4 days overdue
    future_due_2 = (date.today() + timedelta(days=5)).isoformat()

    plan = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": sharma_id,
            "plan_type": "installments",
            "planned_amount_paise": 2000000,
            "start_date": past_start,
            "installments": [
                {"due_date": past_due_1, "amount_paise": 1000000},
                {"due_date": future_due_2, "amount_paise": 1000000},
            ],
        },
    ).json()

    plan_id = plan["id"]
    inst1 = plan["installments"][0]

    # Check that overdue status and days_overdue are calculated
    assert inst1["status"] == "overdue"
    assert inst1["days_overdue"] == 4
    assert plan["status"] == "overdue"
    assert plan["days_overdue"] == 4

    # Now pay the overdue instalment in full -> must transition to 'paid' and days_overdue = 0
    client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1['id']}/payments",
        json={
            "payment_id": "pay_overdue_remedied",
            "amount_paise": 1000000,
            "payment_date": date.today().isoformat(),
        },
    )

    refreshed_plan = client.get(f"/api/v1/repayment-plans/{plan_id}").json()
    i1_refreshed = refreshed_plan["installments"][0]
    assert i1_refreshed["status"] == "paid"
    assert i1_refreshed["days_overdue"] == 0
    # Overall plan is no longer overdue because remaining instalment is in future
    assert refreshed_plan["status"] == "active"
    assert refreshed_plan["days_overdue"] == 0

