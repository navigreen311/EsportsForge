"""API endpoints for EA FC 26 TacticsForge, SkillForge, SetPieceForge."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.eafc26.tactics import (
    CornerRoutine,
    CounterTactic,
    CustomInstruction,
    FormationMeta,
    FreeKickSetup,
    InputTimingResult,
    InstructionPreset,
    PenaltyAnalysis,
    SetPieceReport,
    SkillChain,
    SkillMoveAnalysis,
    SkillTrainingPlan,
    TacticalReport,
)
from app.services.agents.eafc26.tactics_forge import TacticsForge
from app.services.agents.eafc26.skill_forge import SkillForge
from app.services.agents.eafc26.set_piece_forge import SetPieceForge

router = APIRouter(prefix="/titles/eafc26/tactics", tags=["EA FC 26 — Tactics"])

_tactics_engine = TacticsForge()
_skill_engine = SkillForge()
_set_piece_engine = SetPieceForge()


# ---------------------------------------------------------------------------
# Formation meta
# ---------------------------------------------------------------------------

@router.get("/meta", response_model=TacticalReport, summary="Formation meta report")
async def get_formation_meta() -> TacticalReport:
    """Get the current formation meta snapshot."""
    return _tactics_engine.get_formation_meta()


@router.get("/formations/{name}", response_model=FormationMeta, summary="Rate a formation")
async def rate_formation(name: str) -> FormationMeta:
    """Rate a specific formation against the current meta."""
    return _tactics_engine.rate_formation(name)


# ---------------------------------------------------------------------------
# Custom instructions
# ---------------------------------------------------------------------------

@router.get("/instructions", response_model=CustomInstruction, summary="Optimize instructions")
async def optimize_instructions(
    formation: str = Query(..., description="Formation name"),
    playstyle: str = Query("balanced", description="Playstyle preset"),
    opponent_formation: str | None = Query(None, description="Opponent formation"),
) -> CustomInstruction:
    """Generate optimized custom tactical instructions."""
    try:
        return _tactics_engine.optimize_instructions(formation, playstyle, opponent_formation)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/presets", response_model=list[InstructionPreset], summary="List presets")
async def list_presets() -> list[InstructionPreset]:
    """List all available instruction presets."""
    return _tactics_engine.list_presets()


# ---------------------------------------------------------------------------
# Counter tactics
# ---------------------------------------------------------------------------

@router.get("/counter/{opponent_formation}", response_model=CounterTactic, summary="Get counter-tactic")
async def get_counter_tactic(opponent_formation: str) -> CounterTactic:
    """Get counter-tactic for a specific opponent formation."""
    return _tactics_engine.get_counter_tactic(opponent_formation)


@router.get("/counters", response_model=list[CounterTactic], summary="List all counters")
async def list_counters() -> list[CounterTactic]:
    """List all available counter-tactics."""
    return _tactics_engine.list_counter_tactics()


# ---------------------------------------------------------------------------
# Skill moves
# ---------------------------------------------------------------------------

@router.get("/skill/analyze", response_model=SkillMoveAnalysis, summary="Analyze skill move")
async def analyze_skill(
    skill_name: str = Query(...),
    defender_stance: str = Query("standing", description="standing, jockey, press"),
    star_rating: int = Query(5, ge=1, le=5),
) -> SkillMoveAnalysis:
    """Analyze skill move effectiveness against a defensive context."""
    return _skill_engine.analyze_skill_efficiency(skill_name, defender_stance, star_rating)


@router.post("/skill/timing/{user_id}", response_model=InputTimingResult, summary="Evaluate timing")
async def evaluate_timing(
    user_id: str,
    skill_name: str = Query(...),
    input_ms: float = Query(..., ge=0),
) -> InputTimingResult:
    """Evaluate input timing accuracy for a skill move."""
    return _skill_engine.evaluate_timing(user_id, skill_name, input_ms)


@router.get("/skill/chains", response_model=list[SkillChain], summary="Skill chains")
async def get_skill_chains(
    star_rating: int = Query(5, ge=1, le=5),
    max_difficulty: float = Query(1.0, ge=0.0, le=1.0),
) -> list[SkillChain]:
    """Get recommended skill move chains."""
    return _skill_engine.recommend_chains(star_rating, max_difficulty)


@router.get("/skill/training/{user_id}", response_model=SkillTrainingPlan, summary="Skill training plan")
async def get_skill_training(user_id: str) -> SkillTrainingPlan:
    """Generate a personalized skill training plan."""
    return _skill_engine.generate_training_plan(user_id)


# ---------------------------------------------------------------------------
# Set pieces
# ---------------------------------------------------------------------------

@router.get("/set-piece/corner", response_model=CornerRoutine, summary="Corner routine")
async def get_corner_routine(
    tallest_attacker: str = Query("CB"),
    delivery: str = Query("inswinger"),
    opponent_marking: str = Query("man", description="man or zonal"),
) -> CornerRoutine:
    """Build an optimal corner routine."""
    return _set_piece_engine.build_corner_routine(tallest_attacker, delivery, opponent_marking)


@router.get("/set-piece/free-kick", response_model=FreeKickSetup, summary="Free kick setup")
async def get_free_kick(
    distance_yards: float = Query(..., ge=15, le=40),
    fk_accuracy: int = Query(80, ge=0, le=99),
    curve: int = Query(80, ge=0, le=99),
    wall_size: int = Query(4, ge=1, le=6),
) -> FreeKickSetup:
    """Optimize free kick technique for distance and player stats."""
    return _set_piece_engine.optimize_free_kick(distance_yards, fk_accuracy, curve, wall_size)


@router.get("/set-piece/penalty", response_model=PenaltyAnalysis, summary="Penalty analysis")
async def analyze_penalty(
    composure: int = Query(80, ge=0, le=99),
    pressure: str = Query("medium"),
    gk_tendency: str | None = Query(None),
    penalty_number: int = Query(1, ge=1, le=5),
) -> PenaltyAnalysis:
    """Analyze optimal penalty direction under pressure."""
    return _set_piece_engine.analyze_penalty(composure, pressure, gk_tendency, penalty_number)


@router.get("/set-piece/report", response_model=SetPieceReport, summary="Full set piece report")
async def get_set_piece_report(
    tallest_attacker: str = Query("CB"),
    fk_accuracy: int = Query(80, ge=0, le=99),
    curve: int = Query(80, ge=0, le=99),
    composure: int = Query(80, ge=0, le=99),
) -> SetPieceReport:
    """Generate a comprehensive set piece report."""
    return _set_piece_engine.generate_report(tallest_attacker, fk_accuracy, curve, composure)
