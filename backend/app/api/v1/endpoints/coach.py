"""API endpoints for CoachPortal — dashboard, drills, playbooks, war room, seats."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas.coach import (
    CoachDashboard,
    DrillResult,
    SeatManagement,
    SharedPlaybook,
    WarRoom,
)
from app.services.backbone import coach_portal

router = APIRouter(prefix="/coach", tags=["Coach Portal"])


@router.get("/dashboard/{coach_id}", response_model=CoachDashboard, summary="Coach dashboard")
async def get_dashboard(coach_id: str) -> CoachDashboard:
    """Get the coach dashboard overview."""
    return coach_portal.get_coach_dashboard(coach_id)


@router.post("/drills/assign", response_model=DrillResult, summary="Assign drill")
async def assign_drill(
    coach_id: str = Query(...),
    player_id: str = Query(...),
    title: str = Query(...),
    description: str = Query(""),
    drill_type: str = Query("execution"),
    target_metric: str = Query("accuracy"),
    target_value: float = Query(0.8, ge=0, le=1.0),
    due_date: str | None = Query(None),
) -> DrillResult:
    """Assign a targeted drill to a player."""
    return coach_portal.assign_drill(
        coach_id, player_id, title, description, drill_type, target_metric, target_value, due_date,
    )


@router.post("/playbook/share", response_model=SharedPlaybook, summary="Share playbook")
async def share_playbook(
    coach_id: str = Query(...),
    title: str = Query(...),
    game_title: str = Query(...),
    strategies: list[dict[str, Any]] = ...,
    player_ids: list[str] = ...,
    notes: str = Query(""),
) -> SharedPlaybook:
    """Share a playbook with selected players."""
    try:
        return coach_portal.share_playbook(coach_id, title, game_title, strategies, player_ids, notes)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/war-room/{coach_id}", response_model=WarRoom, summary="Get war room")
async def get_war_room(
    coach_id: str,
    game_title: str = Query(...),
) -> WarRoom:
    """Initialize or retrieve a live war room session."""
    return coach_portal.get_war_room(coach_id, game_title)


@router.post("/seats/{coach_id}", response_model=SeatManagement, summary="Manage seats")
async def manage_seats(
    coach_id: str,
    action: str = Query("status", description="status, add_player, remove_player"),
    player_id: str | None = Query(None),
) -> SeatManagement:
    """Manage coach subscription seats."""
    return coach_portal.manage_seats(coach_id, action, player_id)
