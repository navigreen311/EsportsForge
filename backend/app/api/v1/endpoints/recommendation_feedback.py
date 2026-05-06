"""Lightweight follow/dismiss feedback endpoint for dashboard recommendations.

The dashboard's `RecentRecommendations` card POSTs a small action payload
(``{"action": "followed" | "dismissed"}``) when the player taps the Follow or
Dismiss buttons. This module owns that compact contract and persists the
result onto the existing ``Recommendation`` row.

Note: a richer feedback endpoint already lives in ``recommendations.py`` and
accepts a structured ``RecommendationFeedback`` body. This module is mounted
*before* that one in ``router.py`` so the action-shaped POST from the
dashboard is matched here, while the structured shape continues to flow
through the legacy handler when used directly.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.recommendation import Recommendation
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recommendations"])


class FeedbackAction(BaseModel):
    """Compact follow/dismiss action posted by the dashboard."""

    action: Literal["followed", "dismissed"] = Field(
        ...,
        description="Player feedback: 'followed' marks the rec as adopted, "
        "'dismissed' marks it as ignored.",
    )


class FeedbackActionAck(BaseModel):
    """Acknowledgement returned to the dashboard."""

    ok: bool = True
    action: Literal["followed", "dismissed"]
    recommendation_id: uuid.UUID


@router.post(
    "/{recommendation_id}/feedback",
    response_model=FeedbackActionAck,
    status_code=status.HTTP_200_OK,
    summary="Record a follow/dismiss action from the dashboard",
)
async def submit_action_feedback(
    recommendation_id: uuid.UUID,
    payload: FeedbackAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackActionAck:
    """Persist a follow/dismiss action on the player's recommendation row.

    Sets ``was_followed`` (True for ``followed``, False for ``dismissed``) and
    stamps ``feedback_at`` with the current UTC time.
    """
    result = await db.execute(
        select(Recommendation).where(
            Recommendation.id == str(recommendation_id),
            Recommendation.user_id == str(current_user.id),
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    rec.was_followed = payload.action == "followed"
    rec.feedback_at = datetime.now(timezone.utc)

    await db.flush()

    logger.info(
        "Recommendation feedback recorded: id=%s user=%s action=%s",
        recommendation_id,
        current_user.id,
        payload.action,
    )

    return FeedbackActionAck(
        action=payload.action,
        recommendation_id=recommendation_id,
    )
