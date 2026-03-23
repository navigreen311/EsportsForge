"""API endpoints for TransferAI — practice-to-competition transfer analysis."""

from fastapi import APIRouter, Query

from app.schemas.transfer_ai import (
    CompetitionPackage,
    FalseConfidence,
    GameMode,
    ModeComparison,
    TransferRate,
)
from app.services.backbone.transfer_ai import TransferAI

router = APIRouter(prefix="/transfer", tags=["TransferAI"])

_engine = TransferAI()


@router.get("/{user_id}/rates", response_model=TransferRate)
async def get_transfer_rate(
    user_id: str,
    skill: str = Query(..., description="Skill to measure transfer for"),
    from_mode: GameMode = Query(GameMode.LAB, description="Source mode"),
    to_mode: GameMode = Query(GameMode.RANKED, description="Destination mode"),
) -> TransferRate:
    """Measure how well a skill transfers between game modes."""
    return await _engine.measure_transfer_rate(user_id, skill, from_mode, to_mode)


@router.get("/{user_id}/false-confidence", response_model=list[FalseConfidence])
async def get_false_confidence(
    user_id: str,
    title: str = Query(..., description="Game title"),
) -> list[FalseConfidence]:
    """Identify skills that succeed in lab but fail under live pressure."""
    return await _engine.flag_false_confidence(user_id, title)


@router.get("/{user_id}/competition-package", response_model=CompetitionPackage)
async def get_competition_package(
    user_id: str,
    title: str = Query(..., description="Game title"),
) -> CompetitionPackage:
    """Build a gameplan containing only tournament-proven plays."""
    return await _engine.build_competition_ready_package(user_id, title)


@router.get("/{user_id}/mode-comparison", response_model=ModeComparison)
async def get_mode_comparison(
    user_id: str,
    title: str = Query(..., description="Game title"),
) -> ModeComparison:
    """Compare performance across lab, ranked, and tournament modes."""
    return await _engine.get_mode_comparison(user_id, title)
