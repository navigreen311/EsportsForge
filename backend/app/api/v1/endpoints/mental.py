"""Mental API endpoints — confidence, readiness, benchmarks, narrative.

GET /mental/{user_id}/confidence  — Evidence-based confidence score
GET /mental/{user_id}/readiness   — Pre-game readiness assessment
GET /mental/{user_id}/benchmarks  — Percentile benchmarks and dimensions
GET /mental/{user_id}/narrative   — Weekly growth narrative
GET /mental/{user_id}/milestones  — Detected player milestones
GET /mental/{user_id}/growth      — Growth trajectory over time
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.mental import (
    ConfidenceScore,
    GrowthTrajectory,
    Milestone,
    PercentileComparison,
    PreGameReadiness,
    WeeklyNarrative,
)
from app.services.backbone import benchmark_ai, confidence_tracker, narrative_engine

router = APIRouter(prefix="/mental", tags=["mental"])


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------


@router.get("/{user_id}/confidence", response_model=ConfidenceScore)
async def get_confidence(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> ConfidenceScore:
    """Return evidence-based confidence score for a player on a title."""
    try:
        return confidence_tracker.get_confidence_score(user_id, title)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Confidence computation failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


@router.get("/{user_id}/readiness", response_model=PreGameReadiness)
async def get_readiness(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> PreGameReadiness:
    """Return composite pre-game readiness assessment."""
    try:
        return confidence_tracker.get_pre_game_readiness(user_id, title)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Readiness computation failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


@router.get("/{user_id}/benchmarks", response_model=PercentileComparison)
async def get_benchmarks(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. madden26)"),
    percentile: int = Query(95, ge=1, le=100, description="Target percentile to compare against"),
) -> PercentileComparison:
    """Compare player to a target percentile across all dimensions."""
    try:
        return benchmark_ai.compare_to_percentile(user_id, title, percentile)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Benchmark comparison failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------


@router.get("/{user_id}/narrative", response_model=WeeklyNarrative)
async def get_narrative(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. madden26)"),
) -> WeeklyNarrative:
    """Return a coherent weekly growth narrative."""
    try:
        return narrative_engine.generate_weekly_narrative(user_id, title)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Narrative generation failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------


@router.get("/{user_id}/milestones", response_model=list[Milestone])
async def get_milestones(user_id: str) -> list[Milestone]:
    """Detect and return player milestones."""
    try:
        return narrative_engine.detect_milestones(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Milestone detection failed: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------


@router.get("/{user_id}/growth", response_model=GrowthTrajectory)
async def get_growth(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. madden26)"),
    weeks: int = Query(4, ge=1, le=52, description="Number of weeks to analyze"),
) -> GrowthTrajectory:
    """Return growth trajectory trend lines over the specified weeks."""
    try:
        return narrative_engine.get_growth_trajectory(user_id, title, weeks)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Growth trajectory failed: {exc}",
        ) from exc
