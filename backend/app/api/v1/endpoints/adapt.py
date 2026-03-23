"""Adapt endpoints — in-game adaptation and real-time adjustments."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/adapt", tags=["Adaptation"])


@router.post("/{user_id}/suggest")
async def get_adaptation(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Get real-time adaptation suggestions based on current game state."""
    return {"user_id": user_id, "title": title, "adaptations": [], "status": "stub — implementation pending"}


@router.get("/{user_id}/history")
async def get_adaptation_history(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Get history of adaptations made during past sessions."""
    return {"user_id": user_id, "title": title, "history": [], "status": "stub — implementation pending"}


@router.post("/{user_id}/feedback")
async def submit_adaptation_feedback(user_id: str):
    """Submit feedback on whether an adaptation suggestion worked."""
    return {"user_id": user_id, "status": "stub — implementation pending"}
