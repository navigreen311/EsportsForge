"""API endpoints for PGA 2K25 CourseIQ — course strategy and hole analysis."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.pga2k25.course import (
    CourseAnalysis,
    CourseAnalysisRequest,
    HoleStrategy,
)
from app.services.agents.pga2k25.course_iq import CourseIQ

router = APIRouter(prefix="/titles/pga2k25", tags=["PGA 2K25 — CourseIQ"])

_course_iq = CourseIQ()


@router.post(
    "/course/analyze",
    response_model=CourseAnalysis,
    summary="Full 18-hole course strategy",
)
async def analyze_course(body: CourseAnalysisRequest) -> CourseAnalysis:
    """
    Generate a complete 18-hole course strategy with safe vs aggressive
    line EV, hazard risk assessment, and bogey avoidance plans.
    """
    try:
        return await _course_iq.analyze_course(
            user_id=body.user_id,
            course_name=body.course_name,
            tee_box=body.tee_box,
            player_handicap=body.player_handicap,
            risk_tolerance=body.risk_tolerance,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/course/{course_name}/hole/{hole_number}",
    response_model=HoleStrategy,
    summary="Single hole strategy",
)
async def get_hole_strategy(
    course_name: str,
    hole_number: int,
    risk_tolerance: float = 0.5,
) -> HoleStrategy:
    """Get strategy for a single hole including line options and shot plan."""
    if not 1 <= hole_number <= 18:
        raise HTTPException(status_code=400, detail="Hole number must be 1-18")
    try:
        return await _course_iq.get_hole_strategy(
            course_name=course_name,
            hole_number=hole_number,
            risk_tolerance=risk_tolerance,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
