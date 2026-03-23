"""API endpoints for Madden 26 GameplanAI — gameplan generation, kill sheets, meta."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.madden26.gameplan import (
    Gameplan,
    GameplanGenerateRequest,
    KillSheet,
    KillSheetRequest,
    MetaReport,
    Play,
)
from app.services.agents.madden26.gameplan_ai import GameplanAI
from app.services.agents.madden26.meta_bot import MetaBot

router = APIRouter(prefix="/titles/madden26", tags=["Madden 26 — Gameplans"])

_gameplan_ai = GameplanAI()
_meta_bot = MetaBot()

# In-memory store for generated gameplans (replaced by DB in production)
_gameplan_store: dict[uuid.UUID, Gameplan] = {}


@router.post(
    "/gameplan/generate",
    response_model=Gameplan,
    summary="Generate a full gameplan",
)
async def generate_gameplan(body: GameplanGenerateRequest) -> Gameplan:
    """
    Generate a 10-play gameplan tailored to the user's scheme preference,
    opponent tendencies, and roster context. Optionally meta-aware.
    """
    try:
        gameplan = await _gameplan_ai.generate_gameplan(
            user_id=body.user_id,
            opponent_id=body.opponent_id,
            roster=body.roster_context,
            scheme=body.scheme,
            meta_aware=body.meta_aware,
        )
        _gameplan_store[gameplan.id] = gameplan
        return gameplan
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/gameplan/{gameplan_id}",
    response_model=Gameplan,
    summary="Retrieve a generated gameplan",
)
async def get_gameplan(gameplan_id: uuid.UUID) -> Gameplan:
    """Retrieve a previously generated gameplan by its ID."""
    gameplan = _gameplan_store.get(gameplan_id)
    if not gameplan:
        raise HTTPException(status_code=404, detail="Gameplan not found")
    return gameplan


@router.post(
    "/kill-sheet",
    response_model=KillSheet,
    summary="Generate a kill sheet",
)
async def generate_kill_sheet(body: KillSheetRequest) -> KillSheet:
    """Generate 5 plays specifically designed to exploit the given opponent."""
    opponent_data = body.opponent_data or {}
    return await _gameplan_ai.build_kill_sheet(
        opponent_data=opponent_data,
        opponent_id=body.opponent_id,
    )


@router.get(
    "/meta",
    response_model=MetaReport,
    summary="Current Madden 26 meta state",
)
async def get_meta() -> MetaReport:
    """Return the current weekly meta report for Madden 26."""
    return await _meta_bot.scan_weekly_meta()
