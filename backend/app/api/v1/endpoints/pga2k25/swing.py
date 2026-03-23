"""API endpoints for PGA 2K25 SwingForge — swing diagnosis and miss profiles."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.pga2k25.swing import (
    ClubCategory,
    ClubMissProfile,
    SwingDiagnosis,
    SwingDiagnosisRequest,
    SwingSystem,
)
from app.services.agents.pga2k25.swing_forge import SwingForge

router = APIRouter(prefix="/titles/pga2k25", tags=["PGA 2K25 — SwingForge"])

_swing_forge = SwingForge()


@router.post(
    "/swing/diagnose",
    response_model=SwingDiagnosis,
    summary="Full swing diagnosis",
)
async def diagnose_swing(body: SwingDiagnosisRequest) -> SwingDiagnosis:
    """
    Diagnose swing faults, build club-specific miss profiles, and
    analyze pressure drift for the player's swing system.
    """
    try:
        return await _swing_forge.diagnose(
            user_id=body.user_id,
            swing_system=body.swing_system,
            session_ids=body.session_ids,
            include_pressure=body.include_pressure,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/swing/club/{club_category}",
    response_model=ClubMissProfile,
    summary="Club miss profile",
)
async def get_club_miss_profile(
    club_category: ClubCategory,
    swing_system: SwingSystem = SwingSystem.EVOSWING,
) -> ClubMissProfile:
    """Get the miss profile for a specific club category."""
    try:
        from uuid import uuid4
        return await _swing_forge.get_club_profile(
            user_id=uuid4(),
            club_category=club_category,
            swing_system=swing_system,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
