"""API endpoints for Streamer/Analyst Mode (Phase 3 stub)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.backbone import streamer_mode

router = APIRouter(prefix="/streamer", tags=["Streamer Mode"])


@router.get("/overlay/{user_id}")
async def get_broadcast_overlay_config(user_id: str):
    """Retrieve broadcast overlay configuration for a streamer."""
    return streamer_mode.get_broadcast_overlay_config(user_id)


@router.put("/overlay/{user_id}")
async def update_overlay_config(user_id: str, payload: dict[str, Any]):
    """Update broadcast overlay settings."""
    # Get existing config, then merge updates
    config = streamer_mode.get_broadcast_overlay_config(user_id)
    for key, value in payload.items():
        if key in config and key not in ("user_id", "created_at"):
            config[key] = value
    streamer_mode._overlay_configs[user_id] = config
    return config


@router.post("/export/{session_id}")
async def generate_post_game_export(session_id: str):
    """Generate an exportable post-game breakdown for a session."""
    try:
        return streamer_mode.generate_post_game_export(session_id)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/clips/{user_id}")
async def get_clip_queue(user_id: str):
    """Retrieve the clip queue for a user."""
    return streamer_mode.get_clip_queue(user_id)


@router.post("/clips/{clip_id}/export")
async def export_clip(
    clip_id: str,
    format: str = Query("mp4", description="Export format: mp4, gif, webm, png"),
):
    """Export a clip in the specified format."""
    try:
        return streamer_mode.export_clip(clip_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
