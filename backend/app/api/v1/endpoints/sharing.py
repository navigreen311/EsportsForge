"""Sharing endpoints — public gameplan links with token-based access."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.gameplan import Gameplan
from app.models.user import User

router = APIRouter(tags=["Sharing"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: datetime


class SharedGameplanOut(BaseModel):
    title: str
    plays: list[dict[str, Any]] | None = None
    meta_snapshot: str | None = None
    share_views: int = 0
    shared_by: str = "EsportsForge player"


class ImportResponse(BaseModel):
    gameplan_id: str
    message: str


class RevokeResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/gameplans/{gameplan_id}", response_model=ShareResponse)
async def create_share_link(
    gameplan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    """Generate a shareable link for a gameplan (7-day expiry)."""
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == gameplan_id,
            Gameplan.user_id == str(user.id),
        )
    )
    gameplan = result.scalar_one_or_none()
    if not gameplan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gameplan not found")

    token = uuid.uuid4().hex[:12]
    expiry = datetime.now(timezone.utc) + timedelta(days=7)

    gameplan.share_token = token
    gameplan.share_expiry = expiry
    await db.commit()

    return ShareResponse(
        share_token=token,
        share_url=f"/shared/gameplan/{token}",
        expires_at=expiry,
    )


@router.get("/gameplans/{token}", response_model=SharedGameplanOut)
async def get_shared_gameplan(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> SharedGameplanOut:
    """Public endpoint — view a shared gameplan (no auth required)."""
    result = await db.execute(
        select(Gameplan).where(Gameplan.share_token == token)
    )
    gameplan = result.scalar_one_or_none()
    if not gameplan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared gameplan not found")

    if gameplan.share_expiry and gameplan.share_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link has expired")

    gameplan.share_views = (gameplan.share_views or 0) + 1
    await db.commit()

    return SharedGameplanOut(
        title=gameplan.title,
        plays=gameplan.plays,
        meta_snapshot=gameplan.meta_snapshot,
        share_views=gameplan.share_views,
    )


@router.delete("/gameplans/{gameplan_id}", response_model=RevokeResponse)
async def revoke_share(
    gameplan_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RevokeResponse:
    """Revoke a gameplan's share link (auth required)."""
    result = await db.execute(
        select(Gameplan).where(
            Gameplan.id == gameplan_id,
            Gameplan.user_id == str(user.id),
        )
    )
    gameplan = result.scalar_one_or_none()
    if not gameplan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gameplan not found")

    gameplan.share_token = None
    gameplan.share_expiry = None
    await db.commit()

    return RevokeResponse(message="Share link revoked")


@router.post("/gameplans/{token}/import", response_model=ImportResponse)
async def import_shared_gameplan(
    token: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImportResponse:
    """Copy a shared gameplan to the authenticated user's library."""
    result = await db.execute(
        select(Gameplan).where(Gameplan.share_token == token)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared gameplan not found")

    if source.share_expiry and source.share_expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link has expired")

    new_id = str(uuid.uuid4())
    imported = Gameplan(
        id=new_id,
        user_id=str(user.id),
        title=f"{source.title} (imported)",
        plays=source.plays,
        meta_snapshot=source.meta_snapshot,
        is_archived=False,
    )
    db.add(imported)
    await db.commit()

    return ImportResponse(gameplan_id=new_id, message="Gameplan imported successfully")
