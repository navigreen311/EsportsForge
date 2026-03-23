"""ForgeCore recommendation endpoints — AI coaching suggestions with feedback loop."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

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
# Mock store (seeded with sample data)
# ---------------------------------------------------------------------------

_SEED_USER = uuid.UUID("00000000-0000-0000-0000-000000000001")

_recommendations: dict[uuid.UUID, dict] = {}

def _seed() -> None:
    """Populate the mock store with sample recommendations."""
    if _recommendations:
        return
    now = datetime.now(timezone.utc)
    samples = [
        {
            "agent_source": "MetaVersionAgent",
            "recommendation_type": "play_call",
            "title": "madden26",
            "content": {
                "summary": "Switch to Gun Bunch Wk against Cover-3 tendency.",
                "proof": "Opponent ran Cover-3 on 68% of 3rd-and-long situations.",
            },
            "confidence_score": 0.87,
        },
        {
            "agent_source": "OpponentModelAgent",
            "recommendation_type": "counter_strategy",
            "title": "cfb26",
            "content": {
                "summary": "Expect RPO on early downs; crash the DE.",
                "proof": "Last 5 games: RPO rate 72% on 1st down.",
            },
            "confidence_score": 0.74,
        },
    ]
    for s in samples:
        rec_id = uuid.uuid4()
        _recommendations[rec_id] = {
            "id": rec_id,
            "user_id": _SEED_USER,
            "session_id": None,
            "agent_source": s["agent_source"],
            "recommendation_type": s["recommendation_type"],
            "content": s["content"],
            "confidence_score": s["confidence_score"],
            "impact_score": None,
            "was_followed": None,
            "outcome_correct": None,
            "created_at": now,
            "updated_at": now,
        }


_seed()


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
    title: str | None = Query(default=None, description="Filter by game title."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RecommendationListOut:
    """Return a paginated list of the user's ForgeCore recommendations."""
    items = list(_recommendations.values())

    if agent_source:
        items = [r for r in items if r["agent_source"] == agent_source]
    if title:
        items = [r for r in items if r["content"].get("title") == title or r.get("title") == title]

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    return RecommendationListOut(
        items=[RecommendationOut(**r) for r in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationOut,
    summary="Get recommendation detail with proof",
)
async def get_recommendation(recommendation_id: uuid.UUID) -> RecommendationOut:
    """Retrieve a single recommendation, including its proof/reasoning payload."""
    rec = _recommendations.get(recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )
    return RecommendationOut(**rec)


@router.post(
    "/{recommendation_id}/feedback",
    response_model=FeedbackAck,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback on a recommendation",
)
async def submit_feedback(
    recommendation_id: uuid.UUID,
    payload: RecommendationFeedback,
) -> FeedbackAck:
    """Mark a recommendation as followed/ignored and record outcome."""
    rec = _recommendations.get(recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found.",
        )

    rec["was_followed"] = payload.was_followed
    if payload.outcome_correct is not None:
        rec["outcome_correct"] = payload.outcome_correct
    if payload.impact_score is not None:
        rec["impact_score"] = payload.impact_score
    rec["updated_at"] = datetime.now(timezone.utc)

    return FeedbackAck(recommendation_id=recommendation_id)
