"""Gameplan endpoints — strategic play-calling sheet management.

GameplanAI integration: /generate gathers opponent dossier + identity +
ImpactRank priorities + PlayerTwin + recent sessions + meta alert + patch
and feeds them to Claude (or a deterministic mock when no key is set).
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.api_usage import ApiUsage
from app.models.game_session import GameSession
from app.models.gameplan import Gameplan
from app.models.identity_profile import IdentityProfile
from app.models.impact_ranking import ImpactRanking, ImpactStatus
from app.models.meta_alert import GamePatch, MetaAlert
from app.models.opponent import Opponent
from app.models.player_twin import PlayerTwin
from app.models.user import User
from app.services.ai.gameplan_ai import (
    GameplanInputs,
    cache_clear_for_user,
    generate_gameplan,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Gameplans"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GameplanGenerateRequest(BaseModel):
    title: str = Field(max_length=100, description="Game title slug.")
    opponent_id: uuid.UUID | None = None
    mode: str = Field(default="ranked", description="Game mode context.")
    bypass_cache: bool = Field(default=False, description="Force a fresh generation.")
    preferences: dict[str, Any] = Field(default_factory=dict)


class GameplanOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    opponent_id: uuid.UUID | None = None
    plays: list[dict[str, Any]] | None = None
    kill_sheet: dict[str, Any] | None = None
    meta_snapshot: str | None = None
    expires_at: datetime | None = None
    is_archived: bool = False
    share_token: str | None = None
    share_expiry: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameplanGenerateResponse(BaseModel):
    gameplan_id: uuid.UUID
    gameplan: dict[str, Any]
    cached: bool
    source: str


class GameplanListOut(BaseModel):
    items: list[GameplanOut]
    total: int
    page: int
    page_size: int


class GameplanDeleteAck(BaseModel):
    gameplan_id: uuid.UUID
    status: str = "archived"


class GameplanShareOut(BaseModel):
    share_token: str
    share_url_path: str
    expires_at: datetime


class GameplanSharePayload(BaseModel):
    title: str
    opponent_name: str | None
    plays: list[dict[str, Any]] | None
    kill_sheet: dict[str, Any] | None
    meta_snapshot: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Helpers — gather context for GameplanAI
# ---------------------------------------------------------------------------


async def _gather_inputs(
    user: User,
    title: str,
    mode: str,
    opponent_id: str | None,
    db: AsyncSession,
) -> tuple[GameplanInputs, Opponent | None]:
    opponent: Opponent | None = None
    if opponent_id:
        result = await db.execute(select(Opponent).where(Opponent.id == opponent_id))
        opponent = result.scalar_one_or_none()

    identity_q = await db.execute(
        select(IdentityProfile).where(IdentityProfile.user_id == str(user.id))
    )
    identity = identity_q.scalar_one_or_none()

    priorities_q = await db.execute(
        select(ImpactRanking)
        .where(
            ImpactRanking.user_id == str(user.id),
            ImpactRanking.title == title,
            ImpactRanking.status == ImpactStatus.ACTIVE,
        )
        .order_by(ImpactRanking.fix_priority.asc())
        .limit(3)
    )
    priorities = list(priorities_q.scalars().all())

    twin_q = await db.execute(
        select(PlayerTwin).where(
            PlayerTwin.user_id == str(user.id),
            PlayerTwin.title_id == title,
        )
    )
    twin = twin_q.scalar_one_or_none()

    games_q = await db.execute(
        select(GameSession)
        .where(
            GameSession.user_id == str(user.id),
            GameSession.title == title,
            GameSession.opponent_id == (opponent.id if opponent else None),
        )
        .order_by(GameSession.played_at.desc())
        .limit(5)
    )
    recent_games = list(games_q.scalars().all())

    meta_q = await db.execute(
        select(MetaAlert)
        .where(MetaAlert.title_id == title, MetaAlert.status == "published")
        .order_by(MetaAlert.published_at.desc().nullslast())
        .limit(1)
    )
    meta_alert = meta_q.scalar_one_or_none()

    patch_q = await db.execute(
        select(GamePatch)
        .where(GamePatch.title_id == title)
        .order_by(GamePatch.release_date.desc().nullslast())
        .limit(1)
    )
    patch = patch_q.scalar_one_or_none()

    inputs = GameplanInputs(
        user_id=str(user.id),
        title_id=title,
        mode=mode,
        opponent={
            "id": opponent.id,
            "gamertag": opponent.gamertag,
            "archetype": opponent.archetype,
            "tendencies": opponent.tendencies,
            "encounter_count": opponent.encounter_count,
        } if opponent else None,
        identity={
            "offensive_identity": identity.offensive_identity,
            "defensive_philosophy": identity.defensive_philosophy,
            "risk_tolerance": identity.risk_tolerance,
            "pace_preference": identity.pace_preference,
            "comfort_zones": identity.comfort_zones,
            "agent_directness": identity.agent_directness,
        } if identity else None,
        priorities=[
            {
                "fix_priority": p.fix_priority,
                "description": p.description,
                "win_rate_damage": p.win_rate_damage,
                "expected_lift": p.expected_lift,
            }
            for p in priorities
        ],
        player_twin={
            "tendencies": twin.tendencies,
            "execution_ceiling": twin.execution_ceiling,
            "coverage_accuracy": twin.coverage_accuracy,
        } if twin else None,
        recent_games=[
            {
                "played_at": g.played_at.isoformat() if g.played_at else None,
                "result": g.result.value if g.result else None,
                "mode": g.mode.value if g.mode else None,
            }
            for g in recent_games
        ],
        meta_alert={
            "weapon_name": meta_alert.weapon_name,
            "weapon_why": meta_alert.weapon_why,
            "direction": meta_alert.direction,
            "countered_concepts": meta_alert.countered_concepts,
        } if meta_alert else None,
        patch_version=patch.version if patch else None,
    )
    return inputs, opponent


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=GameplanGenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate(
    payload: GameplanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanGenerateResponse:
    """Build a full gameplan via GameplanAI and persist it."""
    if payload.bypass_cache:
        cache_clear_for_user(str(current_user.id))

    inputs, opponent = await _gather_inputs(
        user=current_user,
        title=payload.title,
        mode=payload.mode,
        opponent_id=str(payload.opponent_id) if payload.opponent_id else None,
        db=db,
    )

    result = await generate_gameplan(inputs)
    gp = result.gameplan

    # Persist a Gameplan row with the structured plan blob.
    plan_row = Gameplan(
        user_id=str(current_user.id),
        title=f"vs {opponent.gamertag}" if opponent else f"{payload.title} general plan",
        opponent_id=str(opponent.id) if opponent else None,
        plays=gp.get("plays") or [],
        kill_sheet={
            "kill_sheet": gp.get("killSheet") or [],
            "scriptView": gp.get("scriptView") or [],
            "antiBlitzPackage": gp.get("antiBlitzPackage"),
            "redZonePackage": gp.get("redZonePackage"),
            "twoMinDrill": gp.get("twoMinDrill") or [],
            "opponentSummary": gp.get("opponentSummary"),
            "metaVersion": gp.get("metaVersion"),
            "overallStrategy": gp.get("overallStrategy"),
        },
        meta_snapshot=str(gp.get("metaVersion") or ""),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_archived=False,
    )
    db.add(plan_row)
    await db.flush()

    # Log API usage (best-effort).
    try:
        if not result.cached and result.source == "claude":
            db.add(ApiUsage(
                user_id=str(current_user.id),
                agent="GameplanAI",
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                title_id=payload.title,
                cached=False,
            ))
            await db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("ApiUsage write skipped: %s", exc)

    return GameplanGenerateResponse(
        gameplan_id=plan_row.id,
        gameplan=gp,
        cached=result.cached,
        source=result.source,
    )


@router.get("", response_model=GameplanListOut)
async def list_gameplans(
    title: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanListOut:
    base = select(Gameplan).where(Gameplan.user_id == str(current_user.id))
    if not include_archived:
        base = base.where(Gameplan.is_archived == False)  # noqa: E712
    if title:
        base = base.where(Gameplan.title == title)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    items_q = base.order_by(Gameplan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(items_q)).scalars().all())
    return GameplanListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{gameplan_id}", response_model=GameplanOut)
async def get_gameplan(
    gameplan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanOut:
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == str(gameplan_id),
            Gameplan.user_id == str(current_user.id),
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gameplan not found.")
    return plan


@router.delete("/{gameplan_id}", response_model=GameplanDeleteAck)
async def archive_gameplan(
    gameplan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanDeleteAck:
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == str(gameplan_id),
            Gameplan.user_id == str(current_user.id),
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gameplan not found.")
    plan.is_archived = True
    await db.flush()
    return GameplanDeleteAck(gameplan_id=gameplan_id)


# ---------------------------------------------------------------------------
# Sharing — public 7-day links
# ---------------------------------------------------------------------------


@router.post("/{gameplan_id}/share", response_model=GameplanShareOut)
async def share_gameplan(
    gameplan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanShareOut:
    """Create a public 7-day shareable link for this gameplan."""
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == str(gameplan_id),
            Gameplan.user_id == str(current_user.id),
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gameplan not found.")

    plan.share_token = secrets.token_urlsafe(16)
    plan.share_expiry = datetime.now(timezone.utc) + timedelta(days=7)
    await db.flush()

    return GameplanShareOut(
        share_token=plan.share_token,
        share_url_path=f"/shared/gameplan/{plan.share_token}",
        expires_at=plan.share_expiry,
    )


@router.get("/shared/{token}", response_model=GameplanSharePayload)
async def view_shared_gameplan(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> GameplanSharePayload:
    """Public endpoint — view a gameplan by share token (no auth)."""
    result = await db.execute(select(Gameplan).where(Gameplan.share_token == token))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Shared gameplan not found.")
    if plan.share_expiry and plan.share_expiry < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status.HTTP_410_GONE, "Share link expired.")

    plan.share_views = (plan.share_views or 0) + 1
    await db.flush()

    opponent_name = None
    if plan.opponent_id and plan.opponent:
        opponent_name = plan.opponent.gamertag

    return GameplanSharePayload(
        title=plan.title,
        opponent_name=opponent_name,
        plays=plan.plays,
        kill_sheet=plan.kill_sheet,
        meta_snapshot=plan.meta_snapshot,
        created_at=plan.created_at,
    )
