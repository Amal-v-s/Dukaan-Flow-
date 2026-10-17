"""Unit and API tests for Phase 1F: What-If Simulator.

Verifies:
- Scenario CRUD and event addition
- Baseline vs scenario forecast comparison
- Delta calculations and shortage resolution
- STRICT ISOLATION INVARIANT: Zero mutations to actual database/seed records
"""

import copy
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    seed_service.reset()


def test_scenario_creation_and_listing():
    """Verify creating a custom simulation scenario and listing scenarios."""
    payload = {
        "name": "Test Early Customer Payment",
        "description": "Collect Sharma repayment on 18 Oct",
        "events": [
            {
                "event_type": "customer_collection",
                "source_id": "entry_sharma_01",
                "amount_paise": 1500000,
                "original_date": "2026-10-24",
                "scenario_date": "2026-10-18",
                "description": "Accelerate Sharma collection",
            }
        ],
    }

    create_res = client.post("/api/v1/scenarios", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["name"] == payload["name"]
    assert len(data["events"]) == 1
    scen_id = data["id"]

    # Verify listing includes it
    list_res = client.get("/api/v1/scenarios")
    assert list_res.status_code == 200
    assert any(s["id"] == scen_id for s in list_res.json())


def test_scenario_forecast_resolves_shortage():
    """Verify that shifting Ravi collection earlier and delaying Coastal bill resolves baseline deficit."""
    # Use default mitigation scenario
    res = client.post("/api/v1/scenarios/scen_demo_mitigation/forecast?horizon_days=14")
    assert res.status_code == 200
    data = res.json()

    # Baseline has a shortage: lowest dip is -₹10,000 on 2026-10-20
    assert data["baseline_has_shortage"] is True
    assert data["baseline_lowest_dip_paise"] == -1000000
    assert data["baseline_lowest_dip_date"] == "2026-10-20"

    # Scenario should resolve the shortage: lowest dip is positive and >= 0
    assert data["scenario_has_shortage"] is False
    assert data["scenario_lowest_dip_paise"] > 0
    assert data["shortage_resolved"] is True
    assert data["net_improvement_paise"] > 0

    # Verify delta on the breach date 2026-10-20
    day_20 = next(d for d in data["days"] if d["date"] == "2026-10-20")
    assert day_20["baseline_below_zero"] is True
    assert day_20["scenario_below_zero"] is False
    assert day_20["delta_paise"] > 0  # Massive improvement on day 20


def test_strict_isolation_invariant():
    """Verify that running scenarios NEVER mutates underlying canonical records."""
    # Snapshot actual records before simulation
    biz_before = copy.deepcopy(seed_service.get_business())
    customers_before = copy.deepcopy(seed_service.get_customers())
    bills_before = copy.deepcopy(seed_service.get_supplier_bills())
    txs_before = copy.deepcopy(seed_service.get_transactions())

    # Run heavy simulation with date shifts and extra expenses
    res = client.post("/api/v1/scenarios/scen_demo_mitigation/forecast?horizon_days=14")
    assert res.status_code == 200

    # Also run ad-hoc scenario with large expense
    adhoc_res = client.post(
        "/api/v1/scenarios",
        json={
            "name": "Big Expense Test",
            "events": [
                {
                    "event_type": "extra_expense",
                    "amount_paise": 99999999,
                    "scenario_date": "2026-10-18",
                }
            ],
        },
    )
    adhoc_id = adhoc_res.json()["id"]
    client.post(f"/api/v1/scenarios/{adhoc_id}/forecast")

    # Snapshot actual records after simulations
    biz_after = seed_service.get_business()
    customers_after = seed_service.get_customers()
    bills_after = seed_service.get_supplier_bills()
    txs_after = seed_service.get_transactions()

    # MUST BE 100% IDENTICAL
    assert biz_before == biz_after, "INVARIANT BREACH: Business cash or buffer was mutated!"
    assert customers_before == customers_after, "INVARIANT BREACH: Customer entries were mutated!"
    assert bills_before == bills_after, "INVARIANT BREACH: Supplier bills were mutated!"
    assert txs_before == txs_after, "INVARIANT BREACH: Transactions were mutated!"
