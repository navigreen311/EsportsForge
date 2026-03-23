"""API endpoints for Ratings Update Impact Alerts."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.agents.madden26 import ratings_alerts

router = APIRouter(prefix="/ratings", tags=["Ratings Alerts"])


@router.post("/patch-impact")
async def check_patch_impact(payload: dict[str, Any]):
    """Analyze patch notes for rating changes that affect gameplay."""
    patch_version = payload.get("patch_version")
    if not patch_version:
        raise HTTPException(status_code=400, detail="patch_version is required")
    try:
        return ratings_alerts.check_patch_impact(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/affected-gameplans/{user_id}")
async def get_affected_gameplans(user_id: str, payload: dict[str, Any]):
    """Identify which gameplans are affected by rating changes."""
    changes = payload.get("changes", [])
    if not changes:
        raise HTTPException(status_code=400, detail="changes list is required")
    return ratings_alerts.get_affected_gameplans(user_id, changes)


@router.post("/impact-report")
async def generate_impact_report(payload: dict[str, Any]):
    """Generate a detailed impact report from rating changes."""
    changes = payload.get("changes", [])
    if not changes:
        raise HTTPException(status_code=400, detail="changes list is required")
    return ratings_alerts.generate_impact_report(changes)


@router.post("/auto-adjust/{user_id}")
async def auto_adjust_recommendations(user_id: str, payload: dict[str, Any]):
    """Auto-adjust gameplan recommendations based on rating changes."""
    changes = payload.get("changes", [])
    if not changes:
        raise HTTPException(status_code=400, detail="changes list is required")
    return ratings_alerts.auto_adjust_recommendations(user_id, changes)
