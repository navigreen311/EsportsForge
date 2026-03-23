"""API endpoints for Fortnite BuildForge and EditForge — build + edit training."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.fortnite.gameplay import (
    BuildForgeReport,
    BuildSequenceAnalysis,
    BuildType,
    EditAttempt,
    EditDrillResult,
    EditShape,
    EditSpeedProfile,
)
from app.services.agents.fortnite.build_forge import BuildForgeFN
from app.services.agents.fortnite.edit_forge import EditForge

router = APIRouter(prefix="/titles/fortnite/building", tags=["Fortnite — Building & Editing"])

_build_engine = BuildForgeFN()
_edit_engine = EditForge()


# ---------------------------------------------------------------------------
# BuildForge FN endpoints
# ---------------------------------------------------------------------------


@router.get("/sequences/{build_type}", response_model=list)
async def get_sequence_template(build_type: BuildType):
    """Get the reference template for a build sequence type."""
    try:
        return _build_engine.get_sequence_template(build_type)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{user_id}/analyze", response_model=BuildSequenceAnalysis)
async def analyze_build_sequence(
    user_id: str,
    build_type: BuildType = Query(..., description="Build sequence type"),
    step_times_ms: str = Query(..., description="Comma-separated step times in ms"),
    placement_hits: int = Query(..., ge=0, description="Correct placements"),
    placement_total: int = Query(..., ge=1, description="Total placement attempts"),
) -> BuildSequenceAnalysis:
    """Analyze a single build sequence attempt with anti-cheat verification."""
    times = [int(t.strip()) for t in step_times_ms.split(",") if t.strip()]
    try:
        return _build_engine.analyze_sequence(
            user_id=user_id,
            build_type=build_type,
            step_times_ms=times,
            placement_hits=placement_hits,
            placement_total=placement_total,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{user_id}/report", response_model=BuildForgeReport)
async def generate_build_report(
    user_id: str,
    build_types: str = Query(
        "ramp_wall,90s,waterfall",
        description="Comma-separated build types to include",
    ),
) -> BuildForgeReport:
    """Generate a full BuildForge session report with drill prescriptions.

    This endpoint generates a demo report. In production, analyses
    would be loaded from the database.
    """
    types = [BuildType(t.strip()) for t in build_types.split(",") if t.strip()]

    analyses: list[BuildSequenceAnalysis] = []
    for bt in types:
        template = _build_engine.get_sequence_template(bt)
        target_times = [s.target_time_ms for s in template]
        # Use target times as placeholder for demo
        analysis = _build_engine.analyze_sequence(
            user_id=user_id,
            build_type=bt,
            step_times_ms=[int(t * 1.3) for t in target_times],  # 30% slower than target
            placement_hits=max(1, len(template) - 1),
            placement_total=len(template),
        )
        analyses.append(analysis)

    try:
        return _build_engine.generate_report(user_id, analyses)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# EditForge endpoints
# ---------------------------------------------------------------------------


@router.post("/{user_id}/edit/drill", response_model=EditDrillResult)
async def run_edit_drill(
    user_id: str,
    shapes: str = Query("triangle,arch,door", description="Comma-separated shapes to drill"),
    times_ms: str = Query("200,220,250", description="Comma-separated edit times in ms"),
    pressure: bool = Query(False, description="Whether drills were under pressure"),
) -> EditDrillResult:
    """Evaluate an edit drill session with dynamic calibration and anti-cheat."""
    shape_list = [EditShape(s.strip()) for s in shapes.split(",") if s.strip()]
    time_list = [int(t.strip()) for t in times_ms.split(",") if t.strip()]

    attempts: list[EditAttempt] = []
    for i, shape in enumerate(shape_list):
        time_ms = time_list[i] if i < len(time_list) else time_list[-1]
        attempts.append(EditAttempt(
            shape=shape,
            time_ms=time_ms,
            successful=True,
            under_pressure=pressure,
        ))

    try:
        return _edit_engine.evaluate_drill(user_id, attempts)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}/edit/profile", response_model=EditSpeedProfile)
async def get_edit_profile(
    user_id: str,
) -> EditSpeedProfile:
    """Get current edit speed profile and calibration state.

    Returns a baseline profile. In production, this loads from stored attempts.
    """
    # Demo: generate profile from benchmark data
    demo_attempts = [
        EditAttempt(shape=shape, time_ms=benchmark + 50, successful=True)
        for shape, benchmark in [
            (EditShape.TRIANGLE, 180),
            (EditShape.ARCH, 200),
            (EditShape.DOOR, 220),
            (EditShape.WINDOW, 190),
            (EditShape.HALF_WALL, 160),
        ]
    ]
    try:
        return _edit_engine.build_speed_profile(user_id, demo_attempts)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{user_id}/edit/calibration")
async def get_edit_calibration(user_id: str) -> dict:
    """Get current dynamic calibration state for a user."""
    return _edit_engine.get_calibration(user_id)
