"""API endpoints for PGA 2K25 RankedTours AI + SocietyScout."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.pga2k25.ranked import (
    RankedEnvironment,
    RankedTrackingRequest,
    SocietyPrep,
    SocietyPrepRequest,
    TourReport,
    TourType,
)
from app.services.agents.pga2k25.ranked_tours import RankedToursAI

router = APIRouter(prefix="/titles/pga2k25", tags=["PGA 2K25 — RankedTours"])

_ranked = RankedToursAI()


@router.post(
    "/ranked/status",
    response_model=RankedEnvironment,
    summary="Get ranked environment status",
)
async def get_ranked_status(body: RankedTrackingRequest) -> RankedEnvironment:
    """
    Get current ranked tier, points, win rate, and recent form.
    """
    try:
        return await _ranked.get_ranked_status(
            user_id=body.user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/ranked/report/{tour_type}",
    response_model=TourReport,
    summary="Tour performance report",
)
async def get_tour_report(tour_type: TourType) -> TourReport:
    """Generate a performance report for a specific tour type."""
    from uuid import uuid4
    try:
        return await _ranked.generate_tour_report(
            user_id=uuid4(),
            tour_type=tour_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/society/prepare",
    response_model=SocietyPrep,
    summary="Society event preparation plan",
)
async def prepare_for_society(body: SocietyPrepRequest) -> SocietyPrep:
    """
    Generate a targeted preparation plan for a Society event including
    course-specific notes, scoring target, and risk approach.
    """
    try:
        return await _ranked.prepare_for_society(
            user_id=body.user_id,
            society_name=body.society_name,
            event_name=body.event_name,
            course_name=body.course_name,
            course_condition=body.course_condition,
            field_size=body.field_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
