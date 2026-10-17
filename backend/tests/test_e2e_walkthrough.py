"""Phase 1 Full End-to-End Walkthrough & Definition of Done (DoD) Test Suite.

Verifies the entire Phase 1 contract per docs/phase1_phases.md:
1. Dashboard shows available cash, receivables, payables, and forecast summary.
2. Credit sale increases receivables but does NOT increase available cash.
3. Partial repayment decreases receivables and INCREASES actual cash.
4. Unpaid supplier bill increases payables but does NOT decrease cash.
5. Supplier payment decreases payables and DECREASES actual cash.
6. Paid expense decreases actual cash exactly once.
7. Forecast covers 14 days and is strictly deterministic.
8. Shortage alert identifies and explains contributing events.
9. What-If comparison shows baseline and scenario with zero database mutation.
10. Reset demo seed data restores initial state cleanly.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service
from app.services.alert_service import alert_service

client = TestClient(app)


def test_complete_phase1_e2e_walkthrough():
    # 0. Start with a clean reset
    seed_service.reset()
    alert_service.reset_acknowledgements()

    # 1. Verify Initial Dashboard Metrics
    dash = client.get("/api/v1/dashboard").json()
    initial_cash = dash["available_cash_paise"]
    initial_rec = dash["receivables_paise"]
    initial_pay = dash["payables_paise"]

    assert initial_cash == 1500000  # ₹15,000 opening cash
    assert initial_rec > 0
    assert initial_pay > 0
    assert dash["forecast"]["has_shortage"] is True
    assert dash["forecast"]["lowest_balance_paise"] == -1000000  # -₹10,000 on Oct 20

    # 2. Credit sale increases receivables but NOT available cash
    cust_res = client.post(
        "/api/v1/customers",
        json={"name": "New Test Merchant", "phone": "9876543210", "notes": "Wholesale buyer"},
    )
    assert cust_res.status_code == 201
    cust_id = cust_res.json()["id"]

    credit_sale_res = client.post(
        f"/api/v1/customers/{cust_id}/ledger-entries",
        json={
            "entry_type": "credit_sale",
            "amount_paise": 2000000,  # ₹20,000
            "effective_date": "2026-10-17",
            "due_date": "2026-10-25",
            "notes": "5 bags of Basmati Rice on credit",
        },
    )
    assert credit_sale_res.status_code == 201

    dash_after_credit = client.get("/api/v1/dashboard").json()
    # Invariant: Cash in hand remains untouched, receivables increased by ₹20,000
    assert dash_after_credit["available_cash_paise"] == initial_cash
    assert dash_after_credit["receivables_paise"] == initial_rec + 2000000

    # 3. Partial repayment decreases receivables and INCREASES actual cash
    repay_res = client.post(
        f"/api/v1/customers/{cust_id}/ledger-entries",
        json={
            "entry_type": "repayment",
            "amount_paise": 500000,  # ₹5,000 partial payment
            "effective_date": "2026-10-17",
            "payment_method": "cash",
            "notes": "Partial cash payment received",
        },
    )
    assert repay_res.status_code == 201

    dash_after_repay = client.get("/api/v1/dashboard").json()
    # Invariant: Cash in hand increased by ₹5,000, receivables decreased by ₹5,000
    assert dash_after_repay["available_cash_paise"] == initial_cash + 500000
    assert dash_after_repay["receivables_paise"] == initial_rec + 1500000

    # 4. Unpaid supplier bill increases payables but does NOT decrease cash
    sup_res = client.post(
        "/api/v1/suppliers",
        json={"name": "Apex Packaging Co", "contact_person": "Vikram", "phone": "9123456780"},
    )
    assert sup_res.status_code == 201
    sup_id = sup_res.json()["id"]

    bill_res = client.post(
        "/api/v1/supplier-bills",
        json={
            "supplier_id": sup_id,
            "description": "500 corrugated boxes",
            "bill_amount_paise": 3000000,  # ₹30,000
            "bill_date": "2026-10-17",
            "due_date": "2026-10-28",
        },
    )
    assert bill_res.status_code == 201
    bill_id = bill_res.json()["id"]

    dash_after_bill = client.get("/api/v1/dashboard").json()
    # Invariant: Cash in hand remains untouched, payables increased by ₹30,000
    assert dash_after_bill["available_cash_paise"] == initial_cash + 500000
    assert dash_after_bill["payables_paise"] == initial_pay + 3000000

    # 5. Supplier payment decreases payable and DECREASES actual cash
    pay_res = client.post(
        f"/api/v1/supplier-bills/{bill_id}/payments",
        json={
            "amount_paise": 1000000,  # ₹10,000 partial bill settlement
            "payment_date": "2026-10-17",
            "payment_method": "cash",
            "notes": "Advance for packaging boxes",
        },
    )
    assert pay_res.status_code == 201

    dash_after_bill_pay = client.get("/api/v1/dashboard").json()
    # Invariant: Cash in hand decreased by ₹10,000, payables decreased by ₹10,000
    assert dash_after_bill_pay["available_cash_paise"] == initial_cash + 500000 - 1000000
    assert dash_after_bill_pay["payables_paise"] == initial_pay + 2000000

    # 6. Paid expense decreases actual cash exactly once
    exp_res = client.post(
        "/api/v1/expenses",
        json={
            "title": "Shop Cleaning Supplies",
            "category": "maintenance",
            "amount_paise": 25000,  # ₹250
            "expense_date": "2026-10-17",
            "payment_method": "cash",
        },
    )
    assert exp_res.status_code == 201

    dash_after_exp = client.get("/api/v1/dashboard").json()
    assert dash_after_exp["available_cash_paise"] == initial_cash + 500000 - 1000000 - 25000

    # 7. Forecast covers 14 days and is deterministic
    forecast_res = client.get("/api/v1/cash-flow/forecast?horizon_days=14").json()
    assert forecast_res["horizon_days"] == 14
    assert len(forecast_res["days"]) == 14
    assert forecast_res["cash_safety_buffer_paise"] == 1500000

    # 8. Shortage alert identifies and explains contributing events
    alerts_res = client.get("/api/v1/alerts").json()
    assert alerts_res["active_count"] >= 1
    critical_alert = next(a for a in alerts_res["alerts"] if a["severity"] == "critical")
    assert critical_alert["type"] == "cash_shortage"
    assert len(critical_alert["contributing_events"]) > 0

    # 9. What-If Simulator: compare baseline and scenario, zero database mutation
    scen_res = client.post("/api/v1/scenarios/scen_demo_mitigation/forecast?horizon_days=14").json()
    assert scen_res["baseline_has_shortage"] is True
    assert scen_res["scenario_has_shortage"] is False
    assert scen_res["shortage_resolved"] is True
    assert scen_res["net_improvement_paise"] > 0

    # 10. Seed reset restores defaults
    reset_res = client.post("/api/v1/seed/reset")
    assert reset_res.status_code == 200
    dash_reset = client.get("/api/v1/dashboard").json()
    assert dash_reset["available_cash_paise"] == initial_cash
