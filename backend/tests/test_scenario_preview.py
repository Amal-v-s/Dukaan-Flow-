"""Coverage for the non-persisting, current-date What-If preview flow."""
import copy
from datetime import date

import pytest
from fastapi import HTTPException

from app.schemas.scenario import ScenarioPreviewRequest
from app.services.scenario_service import scenario_service
from app.services.seed_data import seed_service


@pytest.fixture
def demo_state(monkeypatch):
    seed_service.reset()
    monkeypatch.setattr(scenario_service, "_today", lambda: date(2026, 10, 17))
    yield
    seed_service.reset()


def test_event_options_are_real_events_in_the_current_horizon(demo_state):
    result = scenario_service.event_options()
    items_by_id = {item["source_id"]: item for item in result["items"]}

    assert result["today"] == "2026-10-17"
    assert result["horizon_days"] == 14
    assert items_by_id["entry_ravi_1"]["event_type"] == "customer_collection"
    assert items_by_id["entry_ravi_1"]["amount_paise"] == 5_000_000
    assert items_by_id["bill_coastal_101"]["event_type"] == "supplier_bill"
    assert items_by_id["bill_coastal_101"]["scheduled_date"] == "2026-10-20"


def test_event_options_follow_business_today(demo_state, monkeypatch):
    monkeypatch.setattr(scenario_service, "_today", lambda: date(2026, 10, 23))
    ids = {item["source_id"] for item in scenario_service.event_options()["items"]}
    assert "entry_ravi_1" not in ids
    assert "bill_coastal_101" not in ids
    assert "entry_sharma_1" in ids


def test_preview_runs_real_event_change_without_saving_or_mutating(demo_state):
    scenarios_before = {item.id for item in scenario_service.list_scenarios()}
    business_before = copy.deepcopy(seed_service.get_business())
    customers_before = copy.deepcopy(seed_service.get_customers())
    bills_before = copy.deepcopy(seed_service.get_supplier_bills())
    transactions_before = copy.deepcopy(seed_service.get_transactions())

    result = scenario_service.preview_event(ScenarioPreviewRequest(
        event_type="customer_collection",
        source_id="entry_ravi_1",
        amount_paise=5_000_000,
        original_date="2026-10-22",
        scenario_date="2026-10-19",
        description="Ravi Stores collection",
    ))

    assert result.baseline_has_shortage is True
    assert result.scenario_has_shortage is False
    assert result.shortage_resolved is True
    assert {item.id for item in scenario_service.list_scenarios()} == scenarios_before
    assert copy.deepcopy(seed_service.get_business()) == business_before
    assert copy.deepcopy(seed_service.get_customers()) == customers_before
    assert copy.deepcopy(seed_service.get_supplier_bills()) == bills_before
    assert copy.deepcopy(seed_service.get_transactions()) == transactions_before


def test_preview_accepts_hypothetical_expense(demo_state):
    result = scenario_service.preview_event(ScenarioPreviewRequest(
        event_type="extra_expense",
        amount_paise=2_500_000,
        scenario_date="2026-10-19",
        description="Unexpected repair",
    ))
    assert result.scenario_lowest_dip_paise < result.baseline_lowest_dip_paise


@pytest.mark.parametrize("event", [
    ScenarioPreviewRequest(
        event_type="customer_collection", source_id="not-a-real-event", amount_paise=1,
        original_date="2026-10-22", scenario_date="2026-10-19",
    ),
    ScenarioPreviewRequest(
        event_type="extra_expense", amount_paise=1, scenario_date="2026-10-16",
    ),
])
def test_preview_rejects_stale_events_and_dates_outside_horizon(demo_state, event):
    with pytest.raises(HTTPException) as exc_info:
        scenario_service.preview_event(event)
    assert exc_info.value.status_code == 422
