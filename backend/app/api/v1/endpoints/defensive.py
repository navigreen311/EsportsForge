"""Defensive strategy endpoints — DefenseAI gameplan + priority list."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.defensive import DefensiveGameplan, DefensivePriority
from app.models.user import User
from app.services.arsenal_ai import call_claude, parse_json_object
from app.services.defensive_ai import (
    TITLE_DEFENSE_CONTEXT,
    build_defensive_gameplan_system,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Caches
# ---------------------------------------------------------------------------

_gameplan_cache: dict[str, tuple[float, dict[str, Any]]] = {}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DefensiveGameplanBody(BaseModel):
    title_id: str
    opponent_id: str | None = None
    opponent_tendencies: dict[str, Any] | None = None


class DefensivePriorityRow(BaseModel):
    id: str
    rank: int
    name: str
    category: str
    win_rate_damage: float
    expected_lift: float
    impact_score: float
    confidence: float


# ---------------------------------------------------------------------------
# /defensive-gameplan
# ---------------------------------------------------------------------------

@router.post("/defensive-gameplan")
async def generate_defensive_gameplan(
    body: DefensiveGameplanBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate a DefenseAI gameplan for the player vs. an opponent."""
    if body.title_id not in TITLE_DEFENSE_CONTEXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported title_id: {body.title_id}",
        )

    cache_key = f"{current_user.id}::{body.title_id}::{body.opponent_id or '_'}"
    cached = _gameplan_cache.get(cache_key)
    if cached and time.time() - cached[0] < 60 * 5:  # 5 min
        return cached[1]

    # Pull this player's defensive priorities for context.
    priorities = (
        await db.execute(
            select(DefensivePriority)
            .where(
                DefensivePriority.user_id == current_user.id,
                DefensivePriority.title_id == body.title_id,
            )
            .order_by(DefensivePriority.rank.asc())
            .limit(5)
        )
    ).scalars().all()
    priority_payload = [
        {
            "rank": p.rank,
            "name": p.name,
            "category": p.category,
            "win_rate_damage": p.win_rate_damage,
        }
        for p in priorities
    ]

    opponent = (
        {"id": body.opponent_id, "tendencies": body.opponent_tendencies or {}}
        if body.opponent_id or body.opponent_tendencies
        else None
    )

    system = build_defensive_gameplan_system(
        body.title_id, opponent, priority_payload
    )
    raw = await call_claude(
        system=system,
        user_content=(
            f"Generate the defensive gameplan vs "
            f"{opponent['id'] if opponent else 'unknown opponent'}."
        ),
        # 2200 truncated the (now deeper) JSON mid-object → unparseable 502s.
        # 8000 fits the full plan with the plain-language teaching fields, matching
        # the Discover fix.
        max_tokens=8000,
    )
    if not raw:
        # Same convention as discover/trigger — explicit 503 so the UI can
        # show an actionable "set ANTHROPIC_API_KEY" message.
        raise HTTPException(
            status_code=503,
            detail="DefenseAI is unavailable — ANTHROPIC_API_KEY not configured",
        )

    parsed = parse_json_object(raw) or {}
    if not parsed:
        raise HTTPException(
            status_code=502,
            detail="DefenseAI returned no parseable JSON",
        )

    # Persist a snapshot — useful for War Room reads and analytics.
    snapshot = DefensiveGameplan(
        user_id=current_user.id,
        title_id=body.title_id,
        opponent_id=body.opponent_id,
        scheme=str((parsed.get("primary_scheme") or {}).get("name", "Unknown")),
        concepts=(parsed.get("situational_packages") or []),
        adjustments=(parsed.get("adjustment_triggers") or []),
        payload=parsed,
    )
    db.add(snapshot)
    await db.commit()

    _gameplan_cache[cache_key] = (time.time(), parsed)
    return parsed


# ---------------------------------------------------------------------------
# /defensive-priorities
# ---------------------------------------------------------------------------

@router.get("/defensive-priorities", response_model=list[DefensivePriorityRow])
async def list_defensive_priorities(
    title_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DefensivePriorityRow]:
    rows = (
        await db.execute(
            select(DefensivePriority)
            .where(
                DefensivePriority.user_id == current_user.id,
                DefensivePriority.title_id == title_id,
            )
            .order_by(DefensivePriority.rank.asc())
        )
    ).scalars().all()
    return [
        DefensivePriorityRow(
            id=r.id,
            rank=r.rank,
            name=r.name,
            category=r.category,
            win_rate_damage=r.win_rate_damage,
            expected_lift=r.expected_lift,
            impact_score=r.impact_score,
            confidence=r.confidence,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# /defensive-context — title metadata, used by frontend to render tabs
# ---------------------------------------------------------------------------

@router.get("/defensive-context")
async def defensive_context(title_id: str) -> dict[str, Any]:
    ctx = TITLE_DEFENSE_CONTEXT.get(title_id)
    if not ctx:
        raise HTTPException(
            status_code=404,
            detail=f"No defensive context for title: {title_id}",
        )
    return {"title_id": title_id, **ctx}
