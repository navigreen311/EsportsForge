"""API endpoints for VarianceCoach — variance education and tilt management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.video_poker.variance import (
    DeviationCheckRequest,
    DeviationCheckResponse,
    StreakAnalysisRequest,
    StreakAnalysisResponse,
    TiltAssessRequest,
    TiltAssessResponse,
    VarianceExplainRequest,
    VarianceExplainResponse,
    VarianceLesson,
)
from app.services.agents.video_poker.variance_coach import VarianceCoach

router = APIRouter(
    prefix="/titles/video-poker/variance",
    tags=["Video Poker — Variance Coach"],
)

_variance_coach = VarianceCoach()


# --------------------------------------------------------------------------
# POST /titles/video-poker/variance/explain
# --------------------------------------------------------------------------

@router.post("/explain", response_model=VarianceExplainResponse)
async def explain_variance(
    request: VarianceExplainRequest,
) -> VarianceExplainResponse:
    """Get a contextual explanation of variance for the current session."""
    try:
        explanation = _variance_coach.explain_variance(
            request.variant,
            request.hands_played,
            request.current_result,
            request.bet_size,
        )
        return VarianceExplainResponse(explanation=explanation)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/variance/tilt-check
# --------------------------------------------------------------------------

@router.post("/tilt-check", response_model=TiltAssessResponse)
async def assess_tilt(request: TiltAssessRequest) -> TiltAssessResponse:
    """Assess current tilt risk based on session factors."""
    try:
        status = _variance_coach.assess_tilt_risk(
            request.consecutive_losses,
            request.session_loss_pct,
            request.hands_played,
            request.missed_big_hands,
            request.time_playing_minutes,
        )
        return TiltAssessResponse(status=status)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/variance/deviation-check
# --------------------------------------------------------------------------

@router.post("/deviation-check", response_model=DeviationCheckResponse)
async def check_deviation(
    request: DeviationCheckRequest,
) -> DeviationCheckResponse:
    """Detect strategy deviation from baseline accuracy."""
    try:
        alert = _variance_coach.detect_strategy_deviation(
            request.recent_decisions, request.baseline_accuracy,
        )
        return DeviationCheckResponse(alert=alert)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/variance/streak-analysis
# --------------------------------------------------------------------------

@router.post("/streak-analysis", response_model=StreakAnalysisResponse)
async def analyze_streak(
    request: StreakAnalysisRequest,
) -> StreakAnalysisResponse:
    """Analyze winning/losing streaks and assess normality."""
    try:
        analysis = _variance_coach.analyze_streak(
            request.results, request.bet_size,
        )
        return StreakAnalysisResponse(analysis=analysis)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# GET /titles/video-poker/variance/lessons
# --------------------------------------------------------------------------

@router.get("/lessons", response_model=list[VarianceLesson])
async def get_all_lessons() -> list[VarianceLesson]:
    """Get all variance education lessons."""
    return _variance_coach.get_all_lessons()


# --------------------------------------------------------------------------
# GET /titles/video-poker/variance/lessons/{lesson_id}
# --------------------------------------------------------------------------

@router.get("/lessons/{lesson_id}", response_model=VarianceLesson)
async def get_lesson(lesson_id: str) -> VarianceLesson:
    """Get a specific variance education lesson."""
    lesson = _variance_coach.get_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"Lesson '{lesson_id}' not found.")
    return lesson
