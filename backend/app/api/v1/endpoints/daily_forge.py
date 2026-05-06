"""Daily Forge endpoints — per-day completion + streak tracking.

The Daily Forge dashboard card has 4 mission flags. Each flip is PATCHed
to the server. When all 4 become true on the same day for the first time,
we stamp ``completed_at`` and advance the user's streak.
"""

from __future__ import annotations

from datetime import date as _date, datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.daily_forge import DailyForgeCompletion, DailyForgeStreak
from app.models.user import User

router = APIRouter(tags=["DailyForge"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

DailyForgeKey = Literal["drill", "focus", "mental", "meta"]


class DailyForgeStatus(BaseModel):
    """Today's Daily Forge state for the authenticated user."""

    drill_done: bool = False
    focus_done: bool = False
    mental_done: bool = False
    meta_done: bool = False
    all_complete: bool = False
    current_streak: int = 0


class DailyForgePatch(BaseModel):
    key: DailyForgeKey = Field(description="Which mission to toggle.")
    done: bool = Field(description="New value for the flag.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

KEY_TO_COL: dict[str, str] = {
    "drill": "drill_done",
    "focus": "focus_done",
    "mental": "mental_done",
    "meta": "meta_done",
}


def _today() -> _date:
    return datetime.now(timezone.utc).date()


def _all_done(row: DailyForgeCompletion) -> bool:
    return bool(
        row.drill_done and row.focus_done and row.mental_done and row.meta_done
    )


async def _get_or_create_today(
    db: AsyncSession, user_id: str
) -> DailyForgeCompletion:
    today = _today()
    result = await db.execute(
        select(DailyForgeCompletion).where(
            DailyForgeCompletion.user_id == user_id,
            DailyForgeCompletion.date == today,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = DailyForgeCompletion(
            user_id=user_id,
            date=today,
            drill_done=False,
            focus_done=False,
            mental_done=False,
            meta_done=False,
        )
        db.add(row)
        await db.flush()
    return row


async def _get_or_create_streak(
    db: AsyncSession, user_id: str
) -> DailyForgeStreak:
    result = await db.execute(
        select(DailyForgeStreak).where(DailyForgeStreak.user_id == user_id)
    )
    streak = result.scalar_one_or_none()
    if streak is None:
        streak = DailyForgeStreak(
            user_id=user_id,
            current_streak=0,
            last_completed_date=None,
            longest_streak=0,
        )
        db.add(streak)
        await db.flush()
    return streak


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/today",
    response_model=DailyForgeStatus,
    summary="Get today's Daily Forge state for the current user",
)
async def get_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyForgeStatus:
    today = _today()
    row_result = await db.execute(
        select(DailyForgeCompletion).where(
            DailyForgeCompletion.user_id == current_user.id,
            DailyForgeCompletion.date == today,
        )
    )
    row = row_result.scalar_one_or_none()

    streak_result = await db.execute(
        select(DailyForgeStreak).where(DailyForgeStreak.user_id == current_user.id)
    )
    streak = streak_result.scalar_one_or_none()

    if row is None:
        return DailyForgeStatus(
            drill_done=False,
            focus_done=False,
            mental_done=False,
            meta_done=False,
            all_complete=False,
            current_streak=streak.current_streak if streak else 0,
        )

    return DailyForgeStatus(
        drill_done=row.drill_done,
        focus_done=row.focus_done,
        mental_done=row.mental_done,
        meta_done=row.meta_done,
        all_complete=_all_done(row),
        current_streak=streak.current_streak if streak else 0,
    )


@router.patch(
    "/today",
    response_model=DailyForgeStatus,
    summary="Toggle one mission flag for today",
)
async def patch_today(
    payload: DailyForgePatch,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyForgeStatus:
    col = KEY_TO_COL.get(payload.key)
    if col is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_key", "message": f"Unknown key: {payload.key}"},
        )

    row = await _get_or_create_today(db, str(current_user.id))
    streak = await _get_or_create_streak(db, str(current_user.id))

    was_all_done = _all_done(row)
    setattr(row, col, payload.done)
    is_all_done = _all_done(row)

    # Transition: not-complete → complete (first time today)
    if is_all_done and not was_all_done:
        today = _today()
        row.completed_at = datetime.now(timezone.utc)

        yesterday = today - timedelta(days=1)
        if streak.last_completed_date == today:
            # already counted today — leave streak alone
            pass
        elif streak.last_completed_date == yesterday:
            streak.current_streak = (streak.current_streak or 0) + 1
        else:
            streak.current_streak = 1
        streak.last_completed_date = today
        if streak.current_streak > (streak.longest_streak or 0):
            streak.longest_streak = streak.current_streak

    # Reverse transition: complete → not-complete (user un-checked something)
    elif was_all_done and not is_all_done:
        row.completed_at = None

    await db.flush()

    return DailyForgeStatus(
        drill_done=row.drill_done,
        focus_done=row.focus_done,
        mental_done=row.mental_done,
        meta_done=row.meta_done,
        all_complete=is_all_done,
        current_streak=streak.current_streak,
    )
