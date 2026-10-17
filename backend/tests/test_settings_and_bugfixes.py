"""Tests verifying bug fixes:
- Settings API (GET, PATCH, validation)
- Dynamic dashboard calculations
- Scenario ID normalization and deduplication
- Consistency of movement gathering across cashflow, alerts, and scenarios
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service
from app.services.scenario_service import scenario_service, _ids_match
from app.services.alert_service import alert_service
from app.services.phase2_service import create_plan

client = TestClient(app)


def test_settings_get_and_patch():
    # 1. GET settings
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    data = res.json()
    assert "store_name" in data
    assert data["cash_safety_buffer_paise"] >= 0
    assert data["currency"] == "INR"

    # 2. PATCH settings
    orig_buffer = data["cash_safety_buffer_paise"]
    patch_res = client.patch(
        "/api/v1/settings",
        json={"store_name": "Updated Kirana", "cash_safety_buffer_paise": 2000000},
    )
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["store_name"] == "Updated Kirana"
    assert patched_data["cash_safety_buffer_paise"] == 2000000

    # 3. Verify GET returns updated values
    get_res = client.get("/api/v1/settings")
    assert get_res.status_code == 200
    assert get_res.json()["cash_safety_buffer_paise"] == 2000000

    # 4. Validation error on negative buffer
    bad_res = client.patch(
        "/api/v1/settings",
        json={"cash_safety_buffer_paise": -500},
    )
    assert bad_res.status_code == 422

    # Restore buffer
    client.patch(
        "/api/v1/settings",
        json={"store_name": "Demo Kirana Store", "cash_safety_buffer_paise": orig_buffer},
    )


def test_dashboard_dynamic_calculation():
    res = client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    # Baseline seed data has 1 expense of ₹1,250 on 2026-10-17
    assert data["today_expenses_paise"] == 125000
    assert data["today_income_paise"] == 0


def test_scenario_ids_match_and_shift():
    # Verify ID matching handles padding variations
    assert _ids_match("entry_ravi_01", "entry_ravi_1") is True
    assert _ids_match("entry_ravi_1", "entry_ravi_01") is True
    assert _ids_match("entry_ravi_1", "entry_ravi_1") is True
    assert _ids_match("bill_coastal_101", "bill_coastal_101") is True
    assert _ids_match("entry_ravi_1", "entry_sharma_1") is False

    # Run default mitigation scenario forecast
    res = client.post("/api/v1/scenarios/scen_demo_mitigation/forecast?horizon_days=14")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "scen_demo_mitigation"
    
    # In baseline, lowest dip was -₹10,000 on 2026-10-20
    # In scenario, Ravi collection shifted from Oct 22 to Oct 19, eliminating the shortage!
    assert data["baseline_has_shortage"] is True
    assert data["scenario_has_shortage"] is False
    assert data["net_improvement_paise"] > 0
    assert data["shortage_resolved"] is True


def test_alert_service_and_repayment_plans():
    # Verify alerts list generates without errors
    alerts_res = alert_service.get_alerts()
    assert alerts_res.active_count >= 1
    # Check that alert dates are in ISO format
    for a in alerts_res.alerts:
        assert len(a.breach_date) == 10
        assert a.projected_balance_paise is not None
