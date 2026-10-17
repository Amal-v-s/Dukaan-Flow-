"""Unit and API integration tests for Shortage Alerts (Phase 1E)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.alert_service import alert_service
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset seed data and alert acknowledgements before each test."""
    seed_service.reset()
    alert_service.reset_acknowledgements()


def test_get_active_alerts_identifies_shortage():
    """Verify that current baseline forecast identifies the Oct 20 deficit alert."""
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    data = res.json()

    assert data["active_count"] >= 1
    assert data["critical_count"] >= 1

    critical_alert = next(a for a in data["alerts"] if a["severity"] == "critical")
    assert critical_alert["type"] == "cash_shortage"
    assert critical_alert["breach_date"] == "2026-10-20"
    assert critical_alert["projected_balance_paise"] == -1000000
    assert critical_alert["deficit_paise"] == 1000000
    assert critical_alert["acknowledged"] is False

    # Check contributing events
    assert len(critical_alert["contributing_events"]) > 0
    bill_contrib = next(c for c in critical_alert["contributing_events"] if c["source_type"] == "supplier_bill")
    assert "Coastal Wholesale" in bill_contrib["description"]
    assert bill_contrib["amount_paise"] == 2500000


def test_alert_acknowledgement_lifecycle():
    """Verify acknowledging an alert removes it from active list unless requested."""
    res = client.get("/api/v1/alerts")
    alert_id = res.json()["alerts"][0]["id"]

    # Acknowledge the alert
    patch_res = client.patch(f"/api/v1/alerts/{alert_id}", json={"acknowledged": True})
    assert patch_res.status_code == 200
    assert patch_res.json()["acknowledged"] is True

    # Active alerts should no longer include this acknowledged alert
    res2 = client.get("/api/v1/alerts")
    assert not any(a["id"] == alert_id for a in res2.json()["alerts"])

    # If requested with include_acknowledged=true, it should be returned
    res3 = client.get("/api/v1/alerts?include_acknowledged=true")
    ack_alert = next(a for a in res3.json()["alerts"] if a["id"] == alert_id)
    assert ack_alert["acknowledged"] is True
