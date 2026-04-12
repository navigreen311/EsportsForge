"""PlayerTwin Data API — twin profile management endpoints.

GET  /player-twin-data/{user_id}              — full twin profile
POST /player-twin-data/{user_id}/recalibrate  — force recalibration
POST /player-twin-data/{user_id}/reset        — wipe twin profile
POST /player-twin-data/{user_id}/correct      — player overrides
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query

from app.services.ai.player_twin_service import PlayerTwinService

router = APIRouter()

# Singleton service — will be replaced by DI container
_twin_service = PlayerTwinService()


@router.get("/{user_id}")
async def get_player_twin_data(
    user_id: str,
    title: str | None = Query(None, description="Filter by game title (e.g. 'madden26')"),
) -> dict[str, Any]:
    """Return the full PlayerTwin profile for a user.

    If ``title`` is provided, returns only that title's profile.
    Otherwise returns all title profiles.
    """
    return _twin_service.get_twin_profile(user_id, title)


@router.post("/{user_id}/recalibrate")
async def recalibrate_twin(
    user_id: str,
    title: str | None = Body(None, description="Specific title to recalibrate, or omit for all"),
) -> dict[str, Any]:
    """Force a recalibration of the player twin.

    Smooths all belief values toward neutral (0.5) and reduces
    confidence so future sessions have stronger influence.
    """
    return _twin_service.recalibrate(user_id, title)


@router.post("/{user_id}/reset")
async def reset_twin(
    user_id: str,
    title: str | None = Body(None, description="Specific title to reset, or omit for all"),
) -> dict[str, Any]:
    """Reset the player twin profile.

    If ``title`` is provided, only that title's profile is wiped.
    Otherwise all title profiles for the user are removed.
    """
    return _twin_service.reset(user_id, title)


@router.post("/{user_id}/correct")
async def correct_twin(
    user_id: str,
    title: str = Body(..., description="Game title"),
    corrections: list[dict[str, Any]] = Body(
        ...,
        description="List of corrections: [{skill, value, reason}]",
    ),
) -> dict[str, Any]:
    """Apply player-supplied corrections to twin beliefs.

    Each correction overrides the twin's learned belief for a
    specific skill. Use this when the player knows the twin is wrong.
    """
    return _twin_service.correct(user_id, title, corrections)
