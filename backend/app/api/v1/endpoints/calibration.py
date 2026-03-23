"""Calibration endpoints — skill assessment and baseline measurement."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/calibration", tags=["Calibration"])


@router.post("/{user_id}/start")
async def start_calibration(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Start a calibration session to measure skill baselines."""
    return {"user_id": user_id, "title": title, "session_id": None, "status": "stub — implementation pending"}


@router.post("/{user_id}/{session_id}/submit")
async def submit_calibration_data(
    user_id: str,
    session_id: str,
):
    """Submit calibration session results."""
    return {"user_id": user_id, "session_id": session_id, "status": "stub — implementation pending"}


@router.get("/{user_id}/results")
async def get_calibration_results(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Get calibration results and skill baselines."""
    return {"user_id": user_id, "title": title, "baselines": {}, "status": "stub — implementation pending"}
