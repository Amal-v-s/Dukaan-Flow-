from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioDTO,
    ScenarioEventCreate,
    ScenarioEventDTO,
    ScenarioForecastResponse,
)
from app.services.scenario_service import scenario_service

router = APIRouter(prefix="/api/v1/scenarios", tags=["What-If Simulator"])


@router.post("", response_model=ScenarioDTO, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioCreate):
    """Create a new hypothetical simulation scenario."""
    return scenario_service.create_scenario(payload)


@router.get("", response_model=List[ScenarioDTO])
def list_scenarios():
    """List all scenarios."""
    return scenario_service.list_scenarios()


@router.get("/{scenario_id}", response_model=ScenarioDTO)
def get_scenario(scenario_id: str):
    """Retrieve details of a specific scenario."""
    scen = scenario_service.get_scenario(scenario_id)
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen


@router.post("/{scenario_id}/events", response_model=ScenarioEventDTO, status_code=status.HTTP_201_CREATED)
def add_scenario_event(scenario_id: str, payload: ScenarioEventCreate):
    """Add a hypothetical event or date/amount override to a scenario."""
    return scenario_service.add_event(scenario_id, payload)


@router.post("/{scenario_id}/forecast", response_model=ScenarioForecastResponse)
def run_scenario_forecast(
    scenario_id: str,
    horizon_days: int = Query(default=14, ge=1, le=60),
):
    """Run baseline vs scenario forecast comparison through the exact same forecast engine.
    
    Guarantees ZERO mutations to actual customer, supplier, transaction, or business records.
    """
    return scenario_service.run_scenario_forecast(scenario_id, horizon_days=horizon_days)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    success = scenario_service.delete_scenario(scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return None
