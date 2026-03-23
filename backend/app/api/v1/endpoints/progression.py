"""Progression endpoints — skill development tracking and growth analysis."""

from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/progression", tags=["Progression"])


@router.get("/{user_id}/overview")
async def get_progression_overview(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Get overall skill progression overview."""
    return {"user_id": user_id, "title": title, "status": "stub — implementation pending"}


@router.get("/{user_id}/skill/{skill}")
async def get_skill_progression(
    user_id: str,
    skill: str,
    title: str = Query(..., description="Game title"),
):
    """Get detailed progression data for a specific skill."""
    return {"user_id": user_id, "skill": skill, "title": title, "status": "stub — implementation pending"}


@router.get("/{user_id}/milestones")
async def get_milestones(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """List achieved and upcoming milestones."""
    return {"user_id": user_id, "title": title, "milestones": [], "status": "stub — implementation pending"}
