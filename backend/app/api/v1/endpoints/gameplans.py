"""Gameplan endpoints — strategic play-calling sheet management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.gameplan import Gameplan
from app.models.user import User
from app.services.ai.forgecore import forgecore

router = APIRouter(tags=["Gameplans"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GameplanGenerateRequest(BaseModel):
    """Request payload for AI-generated gameplan."""

    title: str = Field(max_length=100, description="Game title slug.")
    opponent_id: uuid.UUID | None = None
    mode: str = Field(default="ranked", description="Game mode context.")
    preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Player style preferences the AI should consider.",
    )


class GameplanOut(BaseModel):
    """Response schema for a gameplan."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    opponent_id: uuid.UUID | None = None
    plays: list[dict[str, Any]] | None = None
    kill_sheet: dict[str, Any] | None = None
    meta_snapshot: str | None = None
    expires_at: datetime | None = None
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameplanListOut(BaseModel):
    """Paginated list of gameplans."""

    items: list[GameplanOut]
    total: int
    page: int
    page_size: int


class GameplanDeleteAck(BaseModel):
    """Acknowledgement of gameplan archival."""

    gameplan_id: uuid.UUID
    status: str = "archived"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GameplanOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a gameplan via GameplanAI",
)
async def generate_gameplan(
    payload: GameplanGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanOut:
    """Call GameplanAI to produce a strategic gameplan with plays and kill sheet."""
    now = datetime.now(timezone.utc)

    # Ask ForgeCore for AI-generated plays
    ai_result = await forgecore.agent_query(
        agent="gameplan",
        message=f"Generate a competitive gameplan for {payload.title} in {payload.mode} mode.",
        context={
            "title": payload.title,
            "mode": payload.mode,
            "opponent_id": str(payload.opponent_id) if payload.opponent_id else None,
            "preferences": payload.preferences,
        },
    )

    ai_data = ai_result.get("data", {})
    plays = ai_data.get("plays")
    kill_sheet = ai_data.get("kill_sheet")
    meta_snapshot = ai_data.get("meta_snapshot", f"Meta snapshot -- {payload.title} ({payload.mode})")

    gameplan = Gameplan(
        user_id=str(current_user.id),
        title=payload.title,
        opponent_id=str(payload.opponent_id) if payload.opponent_id else None,
        plays=plays,
        kill_sheet=kill_sheet,
        meta_snapshot=meta_snapshot,
        expires_at=now + timedelta(days=7),
        is_archived=False,
    )
    db.add(gameplan)
    await db.flush()
    await db.refresh(gameplan)

    return gameplan


@router.get(
    "",
    response_model=GameplanListOut,
    summary="List user's gameplans",
)
async def list_gameplans(
    title: str | None = Query(default=None, description="Filter by game title."),
    include_archived: bool = Query(default=False, description="Include archived gameplans."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanListOut:
    """Return a paginated list of the user's gameplans."""
    base = select(Gameplan).where(Gameplan.user_id == str(current_user.id))

    if not include_archived:
        base = base.where(Gameplan.is_archived == False)  # noqa: E712
    if title:
        base = base.where(Gameplan.title == title)

    # Total count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginated items
    items_q = base.order_by(Gameplan.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    items = list(result.scalars().all())

    return GameplanListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{gameplan_id}",
    response_model=GameplanOut,
    summary="Get gameplan detail with plays and kill sheet",
)
async def get_gameplan(
    gameplan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanOut:
    """Retrieve a single gameplan with full plays and kill sheet."""
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == str(gameplan_id),
            Gameplan.user_id == str(current_user.id),
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameplan not found.",
        )
    return plan


@router.delete(
    "/{gameplan_id}",
    response_model=GameplanDeleteAck,
    summary="Archive a gameplan",
)
async def archive_gameplan(
    gameplan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameplanDeleteAck:
    """Soft-delete (archive) a gameplan. Does not permanently remove data."""
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == str(gameplan_id),
            Gameplan.user_id == str(current_user.id),
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gameplan not found.",
        )

    plan.is_archived = True
    await db.flush()

    return GameplanDeleteAck(gameplan_id=gameplan_id)
