from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoints():
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json() == {"status": "alive"}

    res_ready = client.get("/health/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


def test_dashboard_endpoint():
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "INR"
    assert data["available_cash_paise"] == 1500000
    assert data["receivables_paise"] > 0
    assert data["payables_paise"] > 0
    assert data["forecast"]["has_shortage"] is True
    assert data["forecast"]["lowest_balance_paise"] == -1000000
    assert data["forecast"]["lowest_balance_date"] == "2026-10-20"
    assert len(data["recent_transactions"]) > 0
    assert len(data["upcoming_items"]) > 0


def test_customers_endpoint():
    res = client.get("/api/v1/customers")
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 3
    ravi = next(c for c in data["items"] if c["name"] == "Ravi Stores")
    assert ravi["outstanding_balance_paise"] == 5000000


def test_supplier_bills_endpoint():
    res = client.get("/api/v1/supplier-bills")
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 2
    coastal = next(b for b in data["items"] if b["supplier_name"] == "Coastal Wholesale")
    assert coastal["remaining_amount_paise"] == 2500000
    assert coastal["due_date"] == "2026-10-20"


def test_cashflow_forecast_endpoint():
    res = client.get("/api/v1/cash-flow/forecast?horizon_days=14")
    assert res.status_code == 200
    data = res.json()
    assert data["horizon_days"] == 14
    assert len(data["days"]) == 14
    assert data["shortage_detected"] is True
    assert data["buffer_breached"] is True
    assert data["lowest_dip_paise"] == -1000000
    assert data["lowest_dip_date"] == "2026-10-20"
    # Check that day 2026-10-20 detects below_zero and below_safety_buffer
    day_20 = next(d for d in data["days"] if d["date"] == "2026-10-20")
    assert day_20["below_zero"] is True
    assert day_20["below_safety_buffer"] is True
    assert day_20["closing_balance_paise"] == -1000000
    assert len(day_20["contributors"]) > 0
    assert any(c["source_type"] == "supplier_bill" for c in day_20["contributors"])


def test_seed_reset_endpoint():
    res = client.post("/api/v1/seed/reset")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
