"""InstallAI & ProgressionOS API — install generation and mastery progression."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.install import (
    CallSheet,
    CallSheetRequest,
    InstallPackage,
    InstallRequest,
    MasteryPhase,
    OverloadCheck,
    PhaseProgress,
    ProgressionStep,
    WeeklyRoadmap,
)
from app.services.backbone.install_ai import install_ai_engine
from app.services.backbone.progression_os import progression_os_engine

router = APIRouter(tags=["InstallAI", "ProgressionOS"])


# ---------------------------------------------------------------------------
# InstallAI endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/install/call-sheet",
    response_model=CallSheet,
    summary="Generate a call sheet from a gameplan",
)
async def generate_call_sheet(body: CallSheetRequest) -> CallSheet:
    """Generate a formatted call sheet from gameplan data.

    Converts raw plays into situation-grouped call sheets with audible trees.
    """
    return install_ai_engine.generate_call_sheet(
        gameplan=body.gameplan,
        player_profile=body.player_profile,
    )


@router.post(
    "/install/full-package",
    response_model=InstallPackage,
    summary="Generate a complete install package",
)
async def generate_full_package(body: InstallRequest) -> InstallPackage:
    """Generate a complete install package: call sheet, eBook, audible trees,
    red zone package, and anti-blitz scripts.

    This is the primary InstallAI output — everything a player needs to
    execute a gameplan.
    """
    return install_ai_engine.create_full_install(
        gameplan=body.gameplan,
        player_profile=body.player_profile,
        opponent=body.opponent,
    )


# ---------------------------------------------------------------------------
# ProgressionOS endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/progression/{user_id}/roadmap",
    response_model=WeeklyRoadmap,
    summary="Get weekly install roadmap",
)
async def get_roadmap(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. 'madden26')."),
) -> WeeklyRoadmap:
    """Generate or retrieve the ImpactRank-driven weekly install roadmap.

    Returns a phase-appropriate plan with overload throttling applied.
    """
    return progression_os_engine.generate_weekly_roadmap(user_id, title)


@router.get(
    "/progression/{user_id}/phase",
    response_model=list[PhaseProgress],
    summary="Get mastery phase progress",
)
async def get_phase(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. 'madden26')."),
) -> list[PhaseProgress]:
    """Return mastery progress for all four phases.

    Shows which phase is current, which are unlocked, and percent
    completion for each.
    """
    return progression_os_engine.get_mastery_progress(user_id, title)


@router.get(
    "/progression/{user_id}/next-steps",
    response_model=list[ProgressionStep],
    summary="Get next steps to learn",
)
async def get_next_steps(
    user_id: str,
    title: str = Query(..., description="Game title (e.g. 'madden26')."),
    count: int = Query(3, ge=1, le=10, description="Number of steps to return."),
) -> list[ProgressionStep]:
    """Return the next N things the player should learn or practice.

    Ordered by ImpactRank priority score within the current mastery phase.
    """
    return progression_os_engine.get_next_steps(user_id, title, count)


@router.get(
    "/progression/{user_id}/overload",
    response_model=OverloadCheck,
    summary="Check for install overload",
)
async def check_overload(user_id: str) -> OverloadCheck:
    """Check if the player is being asked to install too much.

    Returns overload status and throttling recommendations.
    """
    return progression_os_engine.check_overload(user_id)
