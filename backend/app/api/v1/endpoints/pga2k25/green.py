"""API endpoints for PGA 2K25 GreenIQ — putting analysis and three-putt risk."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.pga2k25.green import (
    GreenReadRequest,
    GreenSpeed,
    PuttAnalysis,
    ThreePuttRisk,
)
from app.services.agents.pga2k25.green_iq import GreenIQ

router = APIRouter(prefix="/titles/pga2k25", tags=["PGA 2K25 — GreenIQ"])

_green_iq = GreenIQ()


@router.post(
    "/green/analyze",
    response_model=PuttAnalysis,
    summary="Full putting analysis",
)
async def analyze_putt(body: GreenReadRequest) -> PuttAnalysis:
    """
    Generate a complete putting analysis including read, pace control,
    three-putt risk, and pressure putting mode.
    """
    try:
        return await _green_iq.analyze_putt(
            user_id=body.user_id,
            course_name=body.course_name,
            hole_number=body.hole_number,
            distance_feet=body.distance_feet,
            pin_position=body.pin_position,
            green_speed=body.green_speed,
            include_pressure=body.include_pressure,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/green/three-putt-risk",
    response_model=ThreePuttRisk,
    summary="Quick three-putt risk check",
)
async def check_three_putt_risk(
    distance_feet: float,
    green_speed: GreenSpeed = GreenSpeed.MEDIUM,
) -> ThreePuttRisk:
    """Quick three-putt risk assessment for a given distance and green speed."""
    if distance_feet <= 0:
        raise HTTPException(status_code=400, detail="Distance must be positive")
    try:
        return await _green_iq.get_three_putt_risk(
            distance_feet=distance_feet,
            green_speed=green_speed,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
