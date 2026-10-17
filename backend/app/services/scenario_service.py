"""Scenario simulation service.

RULES (from docs/01_PRD.md & docs/06_ENGINEERING_RULES.md):
- What-If simulator is strictly isolated.
- The simulator MUST NEVER MUTATE the actual customer khata, supplier bills, cashbook, or business records.
- Run both baseline and scenario through the exact same deterministic forecast engine.
"""

import copy
import re
import uuid
from datetime import date
from typing import Dict, List, Optional
from fastapi import HTTPException
from app.domain.forecast import generate_forecast
from app.services.forecast_movements import gather_forecast_movements
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioDTO,
    ScenarioEventCreate,
    ScenarioEventDTO,
    ScenarioForecastDayDTO,
    ScenarioForecastResponse,
)
from app.services.seed_data import seed_service
from app.core.tenant_context import get_business_id


def _ids_match(id1: Optional[str], id2: Optional[str]) -> bool:
    if not id1 or not id2:
        return False
    if id1 == id2:
        return True
    return re.sub(r'_0+(\d+)', r'_\1', id1) == re.sub(r'_0+(\d+)', r'_\1', id2)


class ScenarioService:
    def __init__(self):
        pass

    @property
    def _scenarios(self):
        scenarios = seed_service._data.setdefault("scenarios", {})
        if get_business_id() == "biz_demo_kirana" and not scenarios:
            self._initialize_default_scenarios(scenarios)
        return scenarios

    def _initialize_default_scenarios(self, scenarios):
        """Seed a standard recommended scenario for instant merchant demo."""
        default_id = "scen_demo_mitigation"
        scenarios[default_id] = {
            "id": default_id,
            "name": "Advance Ravi Collection + Delay Coastal Bill",
            "description": "Shift Ravi Stores payment earlier by 3 days and request a 5-day extension from Coastal Wholesale.",
            "events": [
                {
                    "id": "evt_ravi_early",
                    "event_type": "customer_collection",
                    "source_id": "entry_ravi_1",
                    "amount_paise": 5000000,
                    "original_date": "2026-10-22",
                    "scenario_date": "2026-10-19",
                    "description": "Collect from Ravi Stores on 19 Oct instead of 22 Oct",
                },
                {
                    "id": "evt_coastal_delay",
                    "event_type": "supplier_bill",
                    "source_id": "bill_coastal_101",
                    "amount_paise": 2500000,
                    "original_date": "2026-10-20",
                    "scenario_date": "2026-10-25",
                    "description": "Defer Coastal Wholesale payment to 25 Oct",
                },
            ],
            "created_at": "2026-10-17T00:00:00Z",
        }

    def create_scenario(self, payload: ScenarioCreate) -> ScenarioDTO:
        scen_id = f"scen_{uuid.uuid4().hex[:8]}"
        events_list = []
        for e in payload.events:
            events_list.append(
                {
                    "id": f"evt_{uuid.uuid4().hex[:8]}",
                    "event_type": e.event_type,
                    "source_id": e.source_id,
                    "amount_paise": e.amount_paise,
                    "original_date": e.original_date,
                    "scenario_date": e.scenario_date,
                    "description": e.description or "",
                }
            )

        item = {
            "id": scen_id,
            "name": payload.name,
            "description": payload.description or "",
            "events": events_list,
            "created_at": "2026-10-17T00:00:00Z",
        }
        self._scenarios[scen_id] = item
        return self._to_dto(item)

    def list_scenarios(self) -> List[ScenarioDTO]:
        return [self._to_dto(s) for s in self._scenarios.values()]

    def get_scenario(self, scenario_id: str) -> Optional[ScenarioDTO]:
        item = self._scenarios.get(scenario_id)
        if not item:
            return None
        return self._to_dto(item)

    def add_event(self, scenario_id: str, event: ScenarioEventCreate) -> ScenarioEventDTO:
        scen = self._scenarios.get(scenario_id)
        if not scen:
            raise HTTPException(status_code=404, detail="Scenario not found")

        evt_id = f"evt_{uuid.uuid4().hex[:8]}"
        evt_dict = {
            "id": evt_id,
            "event_type": event.event_type,
            "source_id": event.source_id,
            "amount_paise": event.amount_paise,
            "original_date": event.original_date,
            "scenario_date": event.scenario_date,
            "description": event.description or "",
        }
        scen["events"].append(evt_dict)
        return ScenarioEventDTO(**evt_dict)

    def delete_scenario(self, scenario_id: str) -> bool:
        if scenario_id in self._scenarios:
            del self._scenarios[scenario_id]
            return True
        return False

    def run_scenario_forecast(
        self, scenario_id: str, horizon_days: int = 14
    ) -> ScenarioForecastResponse:
        scen = self._scenarios.get(scenario_id)
        if not scen:
            raise HTTPException(status_code=404, detail="Scenario not found")

        # Snapshot seed state to verify isolation invariant
        biz_before = copy.deepcopy(seed_service.get_business())
        customers_before = copy.deepcopy(seed_service.get_customers())
        bills_before = copy.deepcopy(seed_service.get_supplier_bills())

        start_date = date.fromisoformat("2026-10-17")
        safety_buffer = biz_before.get("cash_safety_buffer_paise", 1500000)

        # Build baseline movements deterministically
        baseline_inflows, baseline_outflows = gather_forecast_movements(customers_before, bills_before)

        # Run Baseline Forecast
        baseline_res = generate_forecast(
            start_date=start_date,
            opening_cash_paise=biz_before["opening_cash_paise"],
            inflows=baseline_inflows,
            outflows=baseline_outflows,
            safety_buffer_paise=safety_buffer,
            horizon_days=horizon_days,
        )

        # Prepare scenario modified lists
        scenario_inflows = copy.deepcopy(baseline_inflows)
        scenario_outflows = copy.deepcopy(baseline_outflows)

        for evt in scen["events"]:
            evt_type = evt["event_type"]
            source_id = evt.get("source_id")
            amt = evt["amount_paise"]
            scen_date = evt["scenario_date"]
            desc = evt.get("description", "")

            if evt_type == "customer_collection":
                # Find and replace or add
                found = False
                if source_id:
                    for item in scenario_inflows:
                        if _ids_match(item.get("source_id"), source_id):
                            item["date"] = scen_date
                            item["amount_paise"] = amt
                            found = True
                            break
                if not found:
                    scenario_inflows.append({
                        "date": scen_date,
                        "amount_paise": amt,
                        "source_type": "customer_collection",
                        "source_id": source_id or f"scen_in_{uuid.uuid4().hex[:6]}",
                        "description": desc or "Hypothetical collection",
                    })

            elif evt_type == "supplier_bill":
                found = False
                if source_id:
                    for item in scenario_outflows:
                        if _ids_match(item.get("source_id"), source_id):
                            item["date"] = scen_date
                            item["amount_paise"] = amt
                            found = True
                            break
                if not found:
                    scenario_outflows.append({
                        "date": scen_date,
                        "amount_paise": amt,
                        "source_type": "supplier_bill",
                        "source_id": source_id or f"scen_out_{uuid.uuid4().hex[:6]}",
                        "description": desc or "Hypothetical bill shift",
                    })

            elif evt_type == "extra_expense":
                scenario_outflows.append({
                    "date": scen_date,
                    "amount_paise": amt,
                    "source_type": "extra_expense",
                    "source_id": f"scen_exp_{uuid.uuid4().hex[:6]}",
                    "description": desc or "Simulated Expense",
                })

            elif evt_type == "extra_income":
                scenario_inflows.append({
                    "date": scen_date,
                    "amount_paise": amt,
                    "source_type": "extra_income",
                    "source_id": f"scen_inc_{uuid.uuid4().hex[:6]}",
                    "description": desc or "Simulated Extra Cash",
                })

        # Run Scenario Forecast
        scenario_res = generate_forecast(
            start_date=start_date,
            opening_cash_paise=biz_before["opening_cash_paise"],
            inflows=scenario_inflows,
            outflows=scenario_outflows,
            safety_buffer_paise=safety_buffer,
            horizon_days=horizon_days,
        )

        # Verify Strict Isolation Invariant: seed data has not been modified
        biz_after = seed_service.get_business()
        customers_after = seed_service.get_customers()
        bills_after = seed_service.get_supplier_bills()
        assert biz_before == biz_after, "Isolation breach: business was mutated!"
        assert customers_before == customers_after, "Isolation breach: customers were mutated!"
        assert bills_before == bills_after, "Isolation breach: supplier bills were mutated!"

        # Combine day-by-day comparison
        comparison_days: List[ScenarioForecastDayDTO] = []
        for i in range(horizon_days):
            b_day = baseline_res.days[i]
            s_day = scenario_res.days[i]
            delta = s_day.closing_balance_paise - b_day.closing_balance_paise

            comparison_days.append(
                ScenarioForecastDayDTO(
                    date=b_day.date,
                    baseline_closing_paise=b_day.closing_balance_paise,
                    scenario_closing_paise=s_day.closing_balance_paise,
                    delta_paise=delta,
                    baseline_below_zero=b_day.below_zero,
                    scenario_below_zero=s_day.below_zero,
                    baseline_below_buffer=b_day.below_safety_buffer,
                    scenario_below_buffer=s_day.below_safety_buffer,
                )
            )

        net_improvement = scenario_res.lowest_dip_paise - baseline_res.lowest_dip_paise
        shortage_resolved = baseline_res.shortage_detected and not scenario_res.shortage_detected

        return ScenarioForecastResponse(
            scenario_id=scen["id"],
            scenario_name=scen["name"],
            currency="INR",
            horizon_days=horizon_days,
            safety_buffer_paise=safety_buffer,
            baseline_lowest_dip_paise=baseline_res.lowest_dip_paise,
            baseline_lowest_dip_date=baseline_res.lowest_dip_date,
            baseline_has_shortage=baseline_res.shortage_detected,
            scenario_lowest_dip_paise=scenario_res.lowest_dip_paise,
            scenario_lowest_dip_date=scenario_res.lowest_dip_date,
            scenario_has_shortage=scenario_res.shortage_detected,
            net_improvement_paise=net_improvement,
            shortage_resolved=shortage_resolved,
            days=comparison_days,
        )

    def _to_dto(self, data: Dict) -> ScenarioDTO:
        return ScenarioDTO(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            events=[ScenarioEventDTO(**e) for e in data.get("events", [])],
            created_at=data.get("created_at", "2026-10-17T00:00:00Z"),
        )


scenario_service = ScenarioService()
