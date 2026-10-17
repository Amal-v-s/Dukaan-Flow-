"""Unit and API tests for Phase 2D (Budgets), Phase 2E (Reports), and Phase 2F (In-App Reminders)."""

from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    seed_service.reset()


def test_budget_creation_and_threshold_alerts():
    """Verify category budget tracking, spent calculation from paid expenses, and threshold alerts."""
    start_date = "2026-10-01"
    end_date = "2026-10-31"

    # Create monthly budget of ₹2,000 (200,000 paise) for 'utilities'
    budget_payload = {
        "category": "utilities",
        "period_start": start_date,
        "period_end": end_date,
        "budget_amount_paise": 200000,
        "period_type": "monthly",
        "thresholds": [75, 90, 100],
    }
    res = client.post("/api/v1/budgets", json=budget_payload)
    assert res.status_code == 201
    budget = res.json()
    budget_id = budget["id"]

    # Initial seed data has 1 electricity expense of ₹1,250 (125,000 paise)
    # Utilization: 125,000 / 200,000 = 62% (below 75%)
    assert budget["spent_paise"] == 125000
    assert budget["remaining_paise"] == 75000
    assert budget["utilization_percent"] == 62
    assert budget["triggered_thresholds"] == []
    assert not budget["exceeded"]

    # Record additional utility expense of ₹300 (30,000 paise)
    # Total spent: 155,000 / 200,000 = 77% -> triggers [75] threshold
    client.post(
        "/api/v1/expenses",
        json={
            "title": "Water Dispenser Refill",
            "category": "utilities",
            "amount_paise": 30000,
            "expense_date": "2026-10-18",
            "payment_method": "cash",
        },
    )

    budgets_res = client.get("/api/v1/budgets").json()
    b = next(x for x in budgets_res["items"] if x["id"] == budget_id)
    assert b["spent_paise"] == 155000
    assert b["remaining_paise"] == 45000
    assert b["utilization_percent"] == 77
    assert 75 in b["triggered_thresholds"]
    assert not b["exceeded"]

    # Record another expense of ₹600 (60,000 paise) -> spent = 215,000 > 200,000 (exceeded!)
    client.post(
        "/api/v1/expenses",
        json={
            "title": "Extra Generator Fuel",
            "category": "utilities",
            "amount_paise": 60000,
            "expense_date": "2026-10-19",
            "payment_method": "cash",
        },
    )

    budgets_res2 = client.get("/api/v1/budgets").json()
    b2 = next(x for x in budgets_res2["items"] if x["id"] == budget_id)
    assert b2["spent_paise"] == 215000
    assert b2["exceeded"] is True
    assert 100 in b2["triggered_thresholds"]


def test_reports_summary_reconciles_cash_and_ledger():
    """Verify reports summary calculates cash movements, categorized expenses, receivables, and payables."""
    start_date = "2026-10-01"
    end_date = "2026-10-31"

    res = client.get(f"/api/v1/reports/summary?start_date={start_date}&end_date={end_date}")
    assert res.status_code == 200
    report = res.json()

    assert report["start_date"] == start_date
    assert report["end_date"] == end_date
    assert report["cash_inflows_paise"] > 0
    assert report["cash_outflows_paise"] > 0
    assert len(report["expenses_by_category"]) > 0
    assert len(report["receivables"]) > 0
    assert len(report["payables"]) > 0

    # Test bad date order rejection
    bad_res = client.get(f"/api/v1/reports/summary?start_date=2026-10-31&end_date=2026-10-01")
    assert bad_res.status_code == 400


def test_reminders_generation_and_acknowledgement():
    """Verify in-app reminders generation from bills/instalments and acknowledgement."""
    res = client.get("/api/v1/reminders")
    assert res.status_code == 200
    data = res.json()
    assert data["external_delivery"] is False  # Must not send external SMS/WhatsApp
    assert len(data["items"]) > 0

    # Verify each reminder has required fields
    r1 = data["items"][0]
    assert "id" in r1
    assert "type" in r1
    assert "due_date" in r1
    assert "amount_paise" in r1
    assert r1["status"] in ("unread", "read", "acknowledged")

    # Acknowledge the reminder
    ack_res = client.patch(f"/api/v1/reminders/{r1['id']}", json={"status": "acknowledged"})
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"


def test_sub_reports_endpoints():
    """Verify Phase 2E sub-report endpoints for expenses, receivables, and payables."""
    start_date = "2026-10-01"
    end_date = "2026-10-31"

    # 1. Expenses report
    exp_res = client.get(f"/api/v1/reports/expenses?start_date={start_date}&end_date={end_date}")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "items" in exp_data
    assert "total_amount_paise" in exp_data
    assert exp_data["total_amount_paise"] == sum(x["amount_paise"] for x in exp_data["items"])

    # 2. Receivables report
    rec_res = client.get("/api/v1/reports/receivables")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "items" in rec_data
    assert "total_receivables_paise" in rec_data
    assert len(rec_data["items"]) == len(client.get("/api/v1/customers").json()["items"])

    # 3. Payables report
    pay_res = client.get("/api/v1/reports/payables")
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    assert "items" in pay_data
    assert "total_payables_paise" in pay_data
    assert len(pay_data["items"]) > 0

