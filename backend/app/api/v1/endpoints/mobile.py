"""API endpoints for MobileAPI — kill sheets, tournament ops, quick view, push notifications."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.schemas.mobile import (
    MobileKillSheet,
    PushResult,
    QuickView,
    TournamentOps,
)
from app.services.backbone import mobile_api

router = APIRouter(prefix="/mobile", tags=["Mobile API"])


@router.get("/kill-sheet/{user_id}", response_model=MobileKillSheet, summary="Mobile kill sheet")
async def get_kill_sheet(
    user_id: str,
    title: str = Query(...),
    opponent_id: str | None = Query(None),
) -> MobileKillSheet:
    """Get a mobile-optimized kill sheet for quick pre-game reference."""
    return mobile_api.get_mobile_kill_sheet(user_id, title, opponent_id)


@router.get("/tournament/{user_id}/{tournament_id}", response_model=TournamentOps, summary="Tournament ops")
async def get_tournament_ops(user_id: str, tournament_id: str) -> TournamentOps:
    """Get mobile tournament operations view."""
    return mobile_api.get_mobile_tourna_ops(user_id, tournament_id)


@router.get("/quick-view/{user_id}", response_model=QuickView, summary="Quick view")
async def get_quick_view(user_id: str, title: str = Query(...)) -> QuickView:
    """Get the mobile quick view dashboard."""
    return mobile_api.get_quick_view(user_id, title)


@router.post("/push", response_model=PushResult, summary="Send push notification")
async def send_push(
    user_id: str = Query(...),
    title: str = Query(...),
    body: str = Query(...),
    notification_type: str = Query("meta_alert"),
    priority: str = Query("normal"),
    data: dict[str, Any] | None = None,
) -> PushResult:
    """Send a push notification to a user's mobile device."""
    return mobile_api.send_push_notification(user_id, title, body, notification_type, priority, data)
