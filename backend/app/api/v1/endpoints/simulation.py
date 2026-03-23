"""API endpoints for SimLab AI and Dynamic Calibration Engine."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.simulation import (
    CalibrationConfig,
    CalibrationRequest,
    DifficultyAdjustment,
    Scenario,
    SimRequest,
    SimulationResult,
)
from app.services.backbone import dynamic_calibration, sim_lab

router = APIRouter(tags=["SimLab & Calibration"])


# ── SimLab ────────────────────────────────────────────────────────────────


@router.post("/sim/create", response_model=Scenario)
async def create_scenario(req: SimRequest):
    """Create a what-if scenario from a game state."""
    scenario = sim_lab.create_scenario(
        game_state=req.game_state,
        what_if=req.what_if,
    )
    if req.name:
        scenario.name = req.name
    if req.scenario_type:
        scenario.scenario_type = req.scenario_type
    return scenario


@router.post("/sim/run", response_model=SimulationResult)
async def run_simulation(req: SimRequest):
    """Create a scenario and immediately run the simulation."""
    scenario = sim_lab.create_scenario(
        game_state=req.game_state,
        what_if=req.what_if,
    )
    if req.name:
        scenario.name = req.name
    if req.scenario_type:
        scenario.scenario_type = req.scenario_type

    result = sim_lab.simulate(scenario, depth=req.depth)
    return result


@router.get("/sim/library/{title}", response_model=list[Scenario])
async def get_scenario_library(title: str):
    """Return pre-built scenario library for a game title."""
    library = sim_lab.get_scenario_library(title)
    if not library:
        raise HTTPException(status_code=404, detail=f"No scenarios found for title '{title}'")
    return library


@router.post("/sim/save/{user_id}", response_model=Scenario)
async def save_scenario(user_id: str, req: SimRequest):
    """Save a custom scenario for a user."""
    scenario = sim_lab.create_scenario(
        game_state=req.game_state,
        what_if=req.what_if,
    )
    if req.name:
        scenario.name = req.name
    if req.scenario_type:
        scenario.scenario_type = req.scenario_type
    return sim_lab.save_scenario(user_id, scenario)


# ── Calibration ───────────────────────────────────────────────────────────


@router.get("/calibration/{user_id}/{skill}", response_model=CalibrationConfig)
async def get_calibration(user_id: str, skill: str):
    """Get current calibration level for a user + skill."""
    return dynamic_calibration.get_calibration_level(user_id, skill)


@router.post("/calibration/adjust", response_model=DifficultyAdjustment)
async def adjust_calibration(req: CalibrationRequest):
    """Adjust calibration after a training rep."""
    return dynamic_calibration.adjust_after_rep(
        user_id=req.user_id,
        skill=req.skill,
        success=req.success,
    )


@router.post("/calibration/calibrate/{user_id}/{skill}", response_model=CalibrationConfig)
async def calibrate_skill(
    user_id: str,
    skill: str,
    current_ceiling: float = Query(..., ge=0.0, le=1.0, description="Player's measured ceiling"),
):
    """Set calibration based on player's current execution ceiling."""
    return dynamic_calibration.calibrate(user_id, skill, current_ceiling)


@router.get("/calibration/{user_id}/{skill}/coasting", response_model=dict)
async def check_coasting(user_id: str, skill: str):
    """Check if the player is coasting (success rate too high)."""
    coasting = dynamic_calibration.detect_coasting(user_id, skill)
    return {"user_id": user_id, "skill": skill, "coasting": coasting}


@router.get("/calibration/{user_id}/{skill}/frustration", response_model=dict)
async def check_frustration(user_id: str, skill: str):
    """Check if the player is frustrated (success rate too low)."""
    frustrated = dynamic_calibration.detect_frustration(user_id, skill)
    return {"user_id": user_id, "skill": skill, "frustrated": frustrated}
