"""ForgeCore recommendation endpoints — AI coaching suggestions with feedback loop."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.base import get_db
from app.models.recommendation import Recommendation
from app.models.user import User

router = APIRouter(tags=["Recommendations"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RecommendationOut(BaseModel):
    """Response schema for a single recommendation."""

    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID | None = None
    agent_source: str
    recommendation_type: str
    content: dict[str, Any]
    confidence_score: float
    impact_score: float | None = None
    was_followed: bool | None = None
    outcome_correct: bool | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecommendationListOut(BaseModel):
    """Paginated list of recommendations."""

    items: list[RecommendationOut]
    total: int
    page: int
    page_size: int


class RecommendationFeedback(BaseModel):
    """User feedback on a recommendation."""

    was_followed: bool = Field(description="Did the player follow this recommendation?")
    outcome_correct: bool | None = Field(
        default=None,
        description="Was the prediction correct? Null if not yet known.",
    )
    impact_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Player-reported impact score 0-100.",
    )


class FeedbackAck(BaseModel):
    """Acknowledgement of feedback submission."""

    recommendation_id: uuid.UUID
    status: str = "feedback_recorded"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=RecommendationListOut,
    summary="List user's recommendations",
)
async def list_recommendations(
    agent_source: str | None = Query(default=None, description="Filter by agent name."),
    recommendation_type: str | None = Query(default=None, description="Filter by recommendation type."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationListOut:
    """Return a paginated list of the user's ForgeCore recommendations."""
    base = select(Recommendation).where(Recommendation.user_id == str(current_user.id))

    if agent_source:
        base = base.where(Recommendation.agent_source == agent_source)
    if recommendation_type:
        base = base.where(Recommendation.recommendation_type == recommendation_type)

    # Total count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    # Paginated items
    items_q = base.order_by(Recommendation.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(items_q)
    items = list(result.scalars().all())

    return RecommendationListOut(
        items=[RecommendationOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationOut,
    summary="Get recommendation detail with proof",
)
async def get_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecommendationOut:
    """Retrieve a single recommendation, including its proof/reasoning payload."""
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
    return RecommendationOut.model_validate(rec)


@router.post(
    "/{recommendation_id}/feedback",
    response_model=FeedbackAck,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on a recommendation",
)
async def submit_feedback(
    recommendation_id: uuid.UUID,
    payload: RecommendationFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedbackAck:
    """Mark a recommendation as followed/ignored and record outcome."""
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

    rec.was_followed = payload.was_followed
    if payload.outcome_correct is not None:
        rec.outcome_correct = payload.outcome_correct
    if payload.impact_score is not None:
        rec.impact_score = payload.impact_score

    await db.flush()

    return FeedbackAck(recommendation_id=recommendation_id)
