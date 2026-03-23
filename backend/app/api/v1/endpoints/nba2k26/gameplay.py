"""API endpoints for NBA 2K26 gameplay — shot timing, positioning, dribbling, momentum."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.nba2k26.gameplay import (
    ComebackProtocol,
    CourtPosition,
    DefensivePosition,
    DefensiveRole,
    DribbleCombo,
    DribbleMastery,
    IsolationCounter,
    MomentumState,
    PickAndRollCoverage,
    RunDetection,
    ShotFeedback,
    ShotTiming,
    ShotTrainingPlan,
    TimeoutDecision,
)
from app.services.agents.nba2k26.dribble_forge import DribbleForge
from app.services.agents.nba2k26.momentum_manager import MomentumManager
from app.services.agents.nba2k26.positioning_ai import PositioningAI
from app.services.agents.nba2k26.shot_forge import ShotForge

router = APIRouter(prefix="/titles/nba2k26/gameplay", tags=["NBA 2K26 — Gameplay"])

_shot_engine = ShotForge()
_positioning_engine = PositioningAI()
_dribble_engine = DribbleForge()
_momentum_engine = MomentumManager()


# ---------------------------------------------------------------------------
# Shot timing endpoints
# ---------------------------------------------------------------------------

@router.get("/shot/timing/{user_id}", response_model=ShotTiming)
async def analyze_shot_timing(
    user_id: str,
    base: str = Query(..., description="Jump shot base name"),
    release_1: str = Query("Release 1", description="Release 1 animation"),
    release_2: str = Query("Release 1", description="Release 2 animation"),
    blend: int = Query(50, ge=0, le=100, description="Release blend percentage"),
    speed: str = Query("normal", description="Release speed: slow, normal, fast"),
) -> ShotTiming:
    """Analyze timing window for a specific jump shot configuration."""
    try:
        return _shot_engine.analyze_timing(
            user_id, base, release_1, release_2, blend, speed,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/shot/record/{user_id}", response_model=ShotTiming)
async def record_shot(user_id: str, feedback: ShotFeedback) -> ShotTiming:
    """Record a shot attempt and get updated timing stats."""
    try:
        return _shot_engine.record_shot(user_id, feedback)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/shot/training/{user_id}", response_model=ShotTrainingPlan)
async def get_training_plan(
    user_id: str,
    target_green_pct: float = Query(0.6, ge=0.0, le=1.0),
) -> ShotTrainingPlan:
    """Generate a personalized shot training plan."""
    try:
        return _shot_engine.generate_training_plan(user_id, target_green_pct)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Positioning endpoints
# ---------------------------------------------------------------------------

@router.post("/position/evaluate/{user_id}", response_model=DefensivePosition)
async def evaluate_position(
    user_id: str,
    role: DefensiveRole = Query(...),
    current_x: float = Query(..., ge=0, le=94),
    current_y: float = Query(..., ge=0, le=50),
    ball_x: float = Query(..., ge=0, le=94),
    ball_y: float = Query(..., ge=0, le=50),
    man_x: float = Query(..., ge=0, le=94),
    man_y: float = Query(..., ge=0, le=50),
) -> DefensivePosition:
    """Evaluate defensive positioning and get recommendations."""
    try:
        return _positioning_engine.evaluate_position(
            user_id, role,
            CourtPosition(x=current_x, y=current_y),
            CourtPosition(x=ball_x, y=ball_y),
            CourtPosition(x=man_x, y=man_y),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/position/pnr", response_model=PickAndRollCoverage)
async def analyze_pnr(
    coverage_type: str = Query(..., description="Coverage: drop, hedge, switch, blitz, ice"),
    bh_x: float = Query(...), bh_y: float = Query(...),
    scr_x: float = Query(...), scr_y: float = Query(...),
    def_ball_x: float = Query(...), def_ball_y: float = Query(...),
    def_scr_x: float = Query(...), def_scr_y: float = Query(...),
) -> PickAndRollCoverage:
    """Analyze pick-and-roll defensive coverage quality."""
    try:
        return _positioning_engine.analyze_pnr_coverage(
            coverage_type,
            CourtPosition(x=bh_x, y=bh_y),
            CourtPosition(x=scr_x, y=scr_y),
            CourtPosition(x=def_ball_x, y=def_ball_y),
            CourtPosition(x=def_scr_x, y=def_scr_y),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Dribble endpoints
# ---------------------------------------------------------------------------

@router.get("/dribble/combos", response_model=list[DribbleCombo])
async def get_combos(
    min_ball_handle: int = Query(25, ge=25, le=99),
    max_difficulty: float = Query(1.0, ge=0.0, le=1.0),
) -> list[DribbleCombo]:
    """Get available dribble combos filtered by requirements."""
    try:
        return _dribble_engine.get_combos(min_ball_handle, max_difficulty)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/dribble/counters", response_model=list[IsolationCounter])
async def get_iso_counters(
    defender_tendency: str = Query(..., description="Defender tendency to counter"),
) -> list[IsolationCounter]:
    """Get counter combos for a specific defensive tendency."""
    try:
        return _dribble_engine.get_isolation_counters(defender_tendency)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/dribble/mastery/{user_id}", response_model=DribbleMastery)
async def get_dribble_mastery(user_id: str) -> DribbleMastery:
    """Get dribble mastery profile for a user."""
    try:
        return _dribble_engine.get_mastery(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Momentum endpoints
# ---------------------------------------------------------------------------

@router.post("/momentum/update", response_model=MomentumState)
async def update_momentum(
    game_id: str = Query(...),
    quarter: int = Query(..., ge=1, le=4),
    game_clock: str = Query(...),
    user_score: int = Query(..., ge=0),
    opponent_score: int = Query(..., ge=0),
    consecutive_stops: int = Query(0, ge=0),
    consecutive_scores: int = Query(0, ge=0),
) -> MomentumState:
    """Update game momentum state."""
    try:
        return _momentum_engine.update_momentum(
            game_id, quarter, game_clock,
            user_score, opponent_score,
            consecutive_stops, consecutive_scores,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/momentum/run/{game_id}", response_model=RunDetection)
async def detect_run(game_id: str) -> RunDetection:
    """Detect if a scoring run is in progress."""
    try:
        return _momentum_engine.detect_run(game_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/momentum/timeout/{game_id}", response_model=TimeoutDecision)
async def should_timeout(game_id: str) -> TimeoutDecision:
    """Get timeout recommendation for current game state."""
    try:
        return _momentum_engine.should_call_timeout(game_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/momentum/comeback", response_model=ComebackProtocol)
async def get_comeback_protocol(
    deficit: int = Query(..., ge=0),
    time_remaining_seconds: float = Query(..., ge=0),
    quarter: int = Query(4, ge=1, le=4),
) -> ComebackProtocol:
    """Generate comeback strategy for a given deficit and time."""
    try:
        return _momentum_engine.generate_comeback_protocol(
            deficit, time_remaining_seconds, quarter,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
