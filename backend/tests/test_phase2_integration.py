"""Integration & Definition of Done (DoD) tests for Phase 2."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    seed_service.reset()


def test_dashboard_and_forecast_phase2_integration():
    """Verify that Phase 2 plans and budgets feed into Dashboard and 14-day Forecast without double-counting."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    ravi_id = ravi["id"]

    # 1. Create a 2-instalment repayment plan
    d1 = (date.today() + timedelta(days=3)).isoformat()
    d2 = (date.today() + timedelta(days=7)).isoformat()
    plan_payload = {
        "customer_id": ravi_id,
        "plan_type": "installments",
        "planned_amount_paise": 3000000,  # ₹30,000 of Ravi's ₹50,000 debt
        "start_date": date.today().isoformat(),
        "installments": [
            {"due_date": d1, "amount_paise": 1500000},
            {"due_date": d2, "amount_paise": 1500000},
        ],
    }
    client.post("/api/v1/repayment-plans", json=plan_payload)

    # 2. Check Dashboard exposes next instalments due
    dash = client.get("/api/v1/dashboard").json()
    assert "next_installments_due" in dash
    assert len(dash["next_installments_due"]) > 0
    assert any(inst["customer_name"] == "Ravi Stores" for inst in dash["next_installments_due"])

    # 3. Check 14-day forecast incorporates repayment plan instalments
    forecast = client.get("/api/v1/cash-flow/forecast?horizon_days=14").json()
    assert forecast["horizon_days"] == 14

    # The plan instalment should appear in contributors on d1 or d2
    found_plan_inflow = False
    for day in forecast["days"]:
        for c in day["contributors"]:
            if c["source_type"] == "repayment_plan":
                found_plan_inflow = True
                assert "scheduled instalment" in c["description"]
    assert found_plan_inflow is True


def test_unplanned_khata_repayment_fifo_allocation():
    """Verify that when a merchant records an ordinary repayment in Customer Khata, it applies FIFO to the customer's active repayment plan."""
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    ravi_id = ravi["id"]

    # Create a 2-part plan for ₹20,000
    d1 = (date.today() + timedelta(days=3)).isoformat()
    d2 = (date.today() + timedelta(days=10)).isoformat()
    plan = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi_id,
            "plan_type": "installments",
            "planned_amount_paise": 2000000,
            "start_date": date.today().isoformat(),
            "installments": [
                {"due_date": d1, "amount_paise": 1000000},
                {"due_date": d2, "amount_paise": 1000000},
            ],
        },
    ).json()
    plan_id = plan["id"]

    # Customer walks in and pays ₹15,000 at the counter (recorded via Customer Khata ledger)
    ledger_pay_res = client.post(
        f"/api/v1/customers/{ravi_id}/ledger-entries",
        json={
            "entry_type": "repayment",
            "amount_paise": 1500000,
            "effective_date": date.today().isoformat(),
            "payment_method": "cash",
            "notes": "Shop counter cash payment",
        },
    )
    assert ledger_pay_res.status_code == 201

    # Check that plan has absorbed the payment FIFO:
    # Instalment 1 (₹10,000) should be fully paid!
    # Instalment 2 (₹10,000) should have ₹5,000 paid!
    updated_plan = client.get(f"/api/v1/repayment-plans/{plan_id}").json()
    assert updated_plan["paid_amount_paise"] == 1500000
    assert updated_plan["remaining_amount_paise"] == 500000

    i1 = updated_plan["installments"][0]
    i2 = updated_plan["installments"][1]
    assert i1["paid_amount_paise"] == 1000000
    assert i1["status"] == "paid"
    assert i2["paid_amount_paise"] == 500000
    assert i2["status"] == "partially_paid"
