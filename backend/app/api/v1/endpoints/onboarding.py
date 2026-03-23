"""Onboarding endpoints — new user setup and initial assessment."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/{user_id}/start")
async def start_onboarding(user_id: str):
    """Begin the onboarding flow for a new user."""
    return {"user_id": user_id, "step": 1, "status": "stub — implementation pending"}


@router.post("/{user_id}/title-select")
async def select_title(user_id: str):
    """Record the user's primary title selection during onboarding."""
    return {"user_id": user_id, "status": "stub — implementation pending"}


@router.post("/{user_id}/skill-assessment")
async def submit_skill_assessment(user_id: str):
    """Submit initial skill self-assessment for PlayerTwin bootstrapping."""
    return {"user_id": user_id, "status": "stub — implementation pending"}


@router.get("/{user_id}/progress")
async def get_onboarding_progress(user_id: str):
    """Get onboarding completion status."""
    return {"user_id": user_id, "completed": False, "step": 0, "status": "stub — implementation pending"}
