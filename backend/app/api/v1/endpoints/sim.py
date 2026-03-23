"""Simulation endpoints — what-if scenario analysis and outcome simulation."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/sim", tags=["Simulation"])


class SimulationRequest(BaseModel):
    """Generic simulation request."""
    scenario: dict
    iterations: int = 100


@router.post("/{user_id}/run")
async def run_simulation(
    user_id: str,
    body: SimulationRequest,
    title: str = Query(..., description="Game title"),
):
    """Run a what-if simulation scenario."""
    return {
        "user_id": user_id,
        "title": title,
        "iterations": body.iterations,
        "results": {},
        "status": "stub — implementation pending",
    }


@router.get("/{user_id}/history")
async def get_sim_history(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Get past simulation results."""
    return {"user_id": user_id, "title": title, "simulations": [], "status": "stub — implementation pending"}
