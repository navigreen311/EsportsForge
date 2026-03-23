"""API endpoints for MLB The Show 26 hitting, baserunning, Diamond Dynasty, and PlayerTwin."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.mlb26.hitting import (
    BaserunningDecision,
    ClutchProfile,
    CountLeverage,
    DDLineup,
    DDPitchingStaff,
    DDPlayerCard,
    HitTrainingPlan,
    MLBTwinProfile,
    PCIPlacement,
    PitchRecognition,
    StaffAnalysis,
    StolenBaseAnalysis,
    SwingFeedback,
    SwingResult,
    TagUpAnalysis,
    TimingWindow,
    ZoneProfile,
)
from app.services.agents.mlb26.hit_forge import HitForge
from app.services.agents.mlb26.baserunning_ai import BaserunningAI
from app.services.agents.mlb26.diamond_dynasty import DiamondDynastyIQ
from app.services.agents.mlb26.mlb_player_twin import MLBPlayerTwin

router = APIRouter(prefix="/titles/mlb26/hitting", tags=["MLB 26 — Hitting"])

_hit_engine = HitForge()
_baserunning_engine = BaserunningAI()
_dd_engine = DiamondDynastyIQ()
_twin_engine = MLBPlayerTwin()


# ---------------------------------------------------------------------------
# Hitting endpoints
# ---------------------------------------------------------------------------

@router.post("/timing/{user_id}", response_model=TimingWindow, summary="Analyze swing timing")
async def analyze_timing(
    user_id: str,
    pitch_type: str = Query(...),
    swing_ms: float = Query(..., ge=0),
) -> TimingWindow:
    """Evaluate swing timing against optimal window."""
    try:
        return _hit_engine.analyze_timing(user_id, pitch_type, swing_ms)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/pci/{user_id}", response_model=PCIPlacement, summary="PCI placement")
async def optimize_pci(
    user_id: str,
    zone: int = Query(..., ge=1, le=9),
    pitch_type: str = Query("four_seam"),
    count: str = Query("0-0"),
) -> PCIPlacement:
    """Get optimal PCI placement for a target zone."""
    return _hit_engine.optimize_pci(user_id, zone, pitch_type, count)


@router.get("/count/{count}", response_model=CountLeverage, summary="Count leverage")
async def get_count_leverage(count: str) -> CountLeverage:
    """Get leverage value and approach for a count."""
    return _hit_engine.get_count_leverage(count)


@router.post("/swing/{user_id}", response_model=SwingResult, summary="Record swing")
async def record_swing(user_id: str, feedback: SwingFeedback) -> SwingResult:
    """Record a swing attempt and get updated stats."""
    try:
        return _hit_engine.record_swing(user_id, feedback)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/training/{user_id}", response_model=HitTrainingPlan, summary="Hitting training plan")
async def get_training_plan(
    user_id: str,
    target_avg: float = Query(0.300, ge=0.0, le=1.0),
) -> HitTrainingPlan:
    """Generate a personalized hitting training plan."""
    return _hit_engine.generate_training_plan(user_id, target_avg)


# ---------------------------------------------------------------------------
# Baserunning endpoints
# ---------------------------------------------------------------------------

@router.get("/baserunning/steal", response_model=StolenBaseAnalysis, summary="Steal probability")
async def steal_probability(
    target_base: str = Query("second"),
    runner_speed: int = Query(75, ge=0, le=99),
    runner_steal: int = Query(70, ge=0, le=99),
    catcher_arm: int = Query(75, ge=0, le=99),
    pitcher_hold: str = Query("average"),
    count: str = Query("1-1"),
) -> StolenBaseAnalysis:
    """Calculate stolen base success probability."""
    return _baserunning_engine.calculate_steal_probability(
        target_base, runner_speed, runner_steal, catcher_arm, pitcher_hold, "normal", count,
    )


@router.get("/baserunning/go-hold", response_model=BaserunningDecision, summary="Go/hold decision")
async def go_or_hold(
    runner_speed: int = Query(75, ge=0, le=99),
    ball_location: str = Query("outfield"),
    fielder_arm: str = Query("average"),
    outs: int = Query(1, ge=0, le=2),
    run_value: str = Query("tying"),
) -> BaserunningDecision:
    """Get go/hold recommendation on a ball in play."""
    return _baserunning_engine.go_or_hold(runner_speed, ball_location, fielder_arm, outs, run_value)


@router.get("/baserunning/tag-up", response_model=TagUpAnalysis, summary="Tag up decision")
async def tag_up(
    runner_speed: int = Query(75, ge=0, le=99),
    outfield_depth: str = Query("medium"),
    fielder_arm: str = Query("average"),
    outs: int = Query(0, ge=0, le=2),
    base_from: str = Query("third"),
) -> TagUpAnalysis:
    """Decide whether to tag up on a fly ball."""
    return _baserunning_engine.tag_up_decision(runner_speed, outfield_depth, fielder_arm, outs, base_from)


# ---------------------------------------------------------------------------
# Diamond Dynasty endpoints
# ---------------------------------------------------------------------------

@router.post("/dd/lineup", response_model=DDLineup, summary="Build meta lineup")
async def build_lineup(
    cards: list[DDPlayerCard],
    platoon: str = Query("vs_rhp"),
) -> DDLineup:
    """Build the optimal Diamond Dynasty lineup."""
    try:
        return _dd_engine.build_meta_lineup(cards, platoon)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dd/pitching-staff", response_model=DDPitchingStaff, summary="Build pitching staff")
async def build_staff(pitchers: list[DDPlayerCard]) -> DDPitchingStaff:
    """Build optimal pitching rotation and bullpen."""
    try:
        return _dd_engine.optimize_pitching_staff(pitchers)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Player Twin endpoints
# ---------------------------------------------------------------------------

@router.post("/twin/pitch-recognition/{user_id}", response_model=PitchRecognition, summary="Pitch recognition")
async def evaluate_recognition(user_id: str, pitch_log: list[dict]) -> PitchRecognition:
    """Evaluate pitch recognition ability from a pitch log."""
    try:
        return _twin_engine.evaluate_pitch_recognition(user_id, pitch_log)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/twin/zones/{user_id}", response_model=ZoneProfile, summary="Zone profile")
async def get_zone_profile(user_id: str) -> ZoneProfile:
    """Get the player's 9-zone hitting profile."""
    return _twin_engine.build_zone_profile(user_id)


@router.post("/twin/clutch/{user_id}", response_model=ClutchProfile, summary="Clutch RISP")
async def analyze_clutch(user_id: str, at_bats: list[dict]) -> ClutchProfile:
    """Analyze clutch performance with RISP."""
    try:
        return _twin_engine.analyze_clutch_risp(user_id, at_bats)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
