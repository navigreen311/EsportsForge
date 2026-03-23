"""API endpoints for Undisputed career mode — build paths, punch packages, training camps."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.undisputed.boxing import (
    BoxingArchetype,
    CareerBuildPath,
    PunchPackage,
    TrainingCampPlan,
)
from app.services.agents.undisputed.camp_builder import CampBuilder

router = APIRouter(prefix="/titles/undisputed/career", tags=["Undisputed — Career"])

_camp = CampBuilder()


@router.get("/build-path", response_model=CareerBuildPath, summary="Career build path")
async def get_build_path(
    archetype: BoxingArchetype = Query(...),
    current_level: int = Query(1, ge=1),
    points: int = Query(50, ge=0),
) -> CareerBuildPath:
    """Generate an optimal career attribute build path."""
    return _camp.generate_build_path(archetype, current_level, points)


@router.get("/punch-package", response_model=PunchPackage, summary="Punch package")
async def get_punch_package(
    archetype: BoxingArchetype = Query(...),
    focus: str = Query("balanced"),
) -> PunchPackage:
    """Assemble the optimal punch package for an archetype."""
    return _camp.build_punch_package(archetype, focus)


@router.get("/training-camp", response_model=TrainingCampPlan, summary="Training camp plan")
async def get_training_camp(
    player_archetype: BoxingArchetype = Query(...),
    opponent_archetype: BoxingArchetype = Query(...),
    rounds: int = Query(12, ge=4, le=12),
    weeks: int = Query(8, ge=1, le=16),
) -> TrainingCampPlan:
    """Generate a training camp plan for the upcoming opponent."""
    return _camp.plan_training_camp(player_archetype, opponent_archetype, rounds, weeks)
