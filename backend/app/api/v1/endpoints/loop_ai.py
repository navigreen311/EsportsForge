"""LoopAI API endpoints — self-improvement engine.

POST /loop/process-session — Process a completed session
GET  /loop/{user_id}/history — Learning history
GET  /loop/{user_id}/patterns — Detected patterns
GET  /loop/{user_id}/attribution — Failure attribution stats
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.schemas.loop_ai import (
    AttributionDistribution,
    LearningHistoryResponse,
    LoopResult,
    PatternDetectionResponse,
    SessionProcessRequest,
)
from app.services.backbone.loop_ai import LoopAI

router = APIRouter(prefix="/loop", tags=["LoopAI"])

# Singleton service instance — will be replaced by DI container
_loop_ai = LoopAI()


@router.post("/process-session", response_model=LoopResult)
async def process_session(request: SessionProcessRequest) -> LoopResult:
    """Process a completed game session through the full LoopAI pipeline.

    Evaluates every recommendation, attributes failures, pushes updates
    to downstream systems, and detects cross-session patterns.
    """
    try:
        result = _loop_ai.process_session(
            user_id=request.user_id,
            session_id=request.session_id,
            title=request.title,
            session_data=request.session_data,
            recommendations_used=request.recommendations_used,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LoopAI processing failed: {exc}",
        ) from exc


@router.get("/{user_id}/history", response_model=LearningHistoryResponse)
async def get_learning_history(
    user_id: UUID,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> LearningHistoryResponse:
    """Retrieve the learning history for a player on a specific title."""
    results = _loop_ai.get_learning_history(user_id, title)
    return LearningHistoryResponse(
        user_id=user_id,
        title=title,
        results=results,
        total=len(results),
    )


@router.get("/{user_id}/patterns", response_model=PatternDetectionResponse)
async def get_patterns(
    user_id: UUID,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> PatternDetectionResponse:
    """Detect recurring patterns across a player's session history."""
    patterns = _loop_ai.detect_patterns(user_id, title)
    return PatternDetectionResponse(
        user_id=user_id,
        title=title,
        patterns=patterns,
        total=len(patterns),
    )


@router.get("/{user_id}/attribution", response_model=AttributionDistribution)
async def get_attribution_stats(
    user_id: UUID,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> AttributionDistribution:
    """Get failure attribution distribution for a player.

    Shows which failure types are most common and whether the trend
    is improving, stable, or declining.
    """
    history = _loop_ai.get_learning_history(user_id, title)
    if not history:
        raise HTTPException(
            status_code=404,
            detail=f"No learning history found for user {user_id} on {title}",
        )

    all_attributions = []
    for result in history:
        all_attributions.extend(result.attributions)

    if not all_attributions:
        raise HTTPException(
            status_code=404,
            detail=f"No failure attributions found for user {user_id} on {title}",
        )

    engine = _loop_ai._attribution_engine
    distribution = engine.get_attribution_distribution(
        user_id, title, all_attributions
    )
    return distribution
