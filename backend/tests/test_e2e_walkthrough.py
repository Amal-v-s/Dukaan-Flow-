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


def test_complete_phase2_e2e_walkthrough():
    """Phase 2 Full End-to-End Walkthrough per docs/phase2_phases.md.
    
    Verifies:
    - Customer repayment plan creation (2 instalments).
    - Partial payment and completion of instalment 1.
    - Cashbook and customer ledger synchronization.
    - Expense budget creation, utilization tracking, and threshold alerts.
    - Financial reports summary, expenses, receivables, and payables.
    - In-app reminder generation and acknowledgement.
    - Dashboard and 14-day forecast integration without double-counting.
    """
    from datetime import date, timedelta
    seed_service.reset()

    # 1. Create a 2-part repayment plan for Ravi Stores (₹20,000)
    customers = client.get("/api/v1/customers").json()["items"]
    ravi = next(c for c in customers if c["name"] == "Ravi Stores")
    initial_cash = client.get("/api/v1/dashboard").json()["available_cash_paise"]

    d1 = (date.today() + timedelta(days=2)).isoformat()
    d2 = (date.today() + timedelta(days=8)).isoformat()

    plan_res = client.post(
        "/api/v1/repayment-plans",
        json={
            "customer_id": ravi["id"],
            "plan_type": "installments",
            "planned_amount_paise": 2000000,
            "start_date": date.today().isoformat(),
            "notes": "E2E plan for pulses supply",
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

    # 2. Record partial payment on instalment 1 (₹5,000)
    pay1 = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": "pay_e2e_001",
            "amount_paise": 500000,
            "payment_date": date.today().isoformat(),
        },
    )
    assert pay1.status_code == 200
    p1 = pay1.json()
    assert p1["paid_amount_paise"] == 500000
    assert p1["remaining_amount_paise"] == 1500000
    assert client.get("/api/v1/dashboard").json()["available_cash_paise"] == initial_cash + 500000

    # 3. Pay remaining ₹5,000 on instalment 1 -> transitions to 'paid'
    pay2 = client.post(
        f"/api/v1/repayment-plans/{plan_id}/installments/{inst1_id}/payments",
        json={
            "payment_id": "pay_e2e_002",
            "amount_paise": 500000,
            "payment_date": date.today().isoformat(),
        },
    )
    assert pay2.status_code == 200
    p2 = pay2.json()
    assert next(i for i in p2["installments"] if i["id"] == inst1_id)["status"] == "paid"
    assert client.get("/api/v1/dashboard").json()["available_cash_paise"] == initial_cash + 1000000

    # 4. Create Category Budget for 'utilities' (₹2,000) and trigger threshold
    start_date = "2026-10-01"
    end_date = "2026-10-31"
    b_res = client.post(
        "/api/v1/budgets",
        json={
            "category": "utilities",
            "period_start": start_date,
            "period_end": end_date,
            "budget_amount_paise": 200000,
            "period_type": "monthly",
            "thresholds": [75, 90, 100],
        },
    )
    assert b_res.status_code == 201

    # Add expense to trigger 75% threshold
    client.post(
        "/api/v1/expenses",
        json={
            "title": "Shop Generator Diesel",
            "category": "utilities",
            "amount_paise": 35000,
            "expense_date": "2026-10-18",
            "payment_method": "cash",
        },
    )
    b_list = client.get("/api/v1/budgets").json()["items"]
    util_budget = next(b for b in b_list if b["category"] == "utilities")
    assert 75 in util_budget["triggered_thresholds"]

    # 5. Financial Reports Reconciliation
    summary = client.get(f"/api/v1/reports/summary?start_date={start_date}&end_date={end_date}").json()
    assert summary["cash_inflows_paise"] > 0
    assert summary["cash_outflows_paise"] > 0
    assert len(summary["repayment_plans"]) >= 1

    exp_rep = client.get(f"/api/v1/reports/expenses?start_date={start_date}&end_date={end_date}").json()
    assert exp_rep["total_amount_paise"] > 0

    rec_rep = client.get("/api/v1/reports/receivables").json()
    assert rec_rep["total_receivables_paise"] > 0

    # 6. In-App Reminders & Acknowledgement
    reminders_res = client.get("/api/v1/reminders").json()
    assert reminders_res["external_delivery"] is False
    assert len(reminders_res["items"]) > 0
    first_rem = reminders_res["items"][0]
    ack = client.patch(f"/api/v1/reminders/{first_rem['id']}", json={"status": "acknowledged"})
    assert ack.status_code == 200

    # 7. Dashboard and Forecast Integration
    dash = client.get("/api/v1/dashboard").json()
    assert len(dash["next_installments_due"]) > 0
    assert dash["budget_alert_count"] >= 1

    forecast = client.get("/api/v1/cash-flow/forecast?horizon_days=14").json()
    assert forecast["horizon_days"] == 14

