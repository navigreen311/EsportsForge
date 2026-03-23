"""API endpoints for Undisputed boxing — archetypes, footwork, combos, scoring, damage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.undisputed.boxing import (
    ArchetypeClassification,
    BodyWorkROI,
    BoxingArchetype,
    ComboAnalysis,
    CutOffAngle,
    DamageState,
    DamageTimeline,
    FightGameplan,
    GuardBreakReport,
    JabEconomyReport,
    PunchEconomyReport,
    PunchType,
    RingPositionAnalysis,
    RingZone,
    RopeTracker,
    RoundBankStrategy,
    RoundScore,
    ScorecardProjection,
    StanceMatchup,
    StanceType,
)
from app.services.agents.undisputed.boxing_iq import BoxingIQ
from app.services.agents.undisputed.footwork_forge import FootworkForge
from app.services.agents.undisputed.combo_ev import ComboEV
from app.services.agents.undisputed.judge_mind import JudgeMind
from app.services.agents.undisputed.damage_narrative import DamageNarrative

router = APIRouter(prefix="/titles/undisputed/boxing", tags=["Undisputed — Boxing"])

_boxing_iq = BoxingIQ()
_footwork = FootworkForge()
_combo = ComboEV()
_judge = JudgeMind()
_damage = DamageNarrative()


# ---------------------------------------------------------------------------
# BoxingIQ endpoints
# ---------------------------------------------------------------------------

@router.post("/archetype", response_model=ArchetypeClassification, summary="Classify archetype")
async def classify_archetype(fight_stats: dict) -> ArchetypeClassification:
    """Classify a fighter into an archetype from their statistics."""
    try:
        return _boxing_iq.classify_archetype(fight_stats)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/stance-matchup", response_model=StanceMatchup, summary="Stance matchup")
async def analyze_stance(
    player_stance: StanceType = Query(...),
    opponent_stance: StanceType = Query(...),
) -> StanceMatchup:
    """Analyze the stance matchup between two fighters."""
    return _boxing_iq.analyze_stance_matchup(player_stance, opponent_stance)


@router.get("/gameplan", response_model=FightGameplan, summary="Fight gameplan")
async def generate_gameplan(
    player_archetype: BoxingArchetype = Query(...),
    opponent_archetype: BoxingArchetype = Query(...),
    player_stance: StanceType = Query(StanceType.ORTHODOX),
    opponent_stance: StanceType = Query(StanceType.ORTHODOX),
    rounds: int = Query(12, ge=4, le=12),
) -> FightGameplan:
    """Generate a comprehensive fight gameplan."""
    return _boxing_iq.generate_gameplan(
        player_archetype, opponent_archetype, player_stance, opponent_stance, rounds,
    )


@router.post("/patterns", summary="Identify patterns")
async def identify_patterns(round_data: list[dict]) -> list[dict]:
    """Identify opponent patterns from round data."""
    return _boxing_iq.identify_patterns(round_data)


# ---------------------------------------------------------------------------
# FootworkForge endpoints
# ---------------------------------------------------------------------------

@router.get("/position", response_model=RingPositionAnalysis, summary="Analyze ring position")
async def analyze_position(
    px: float = Query(..., ge=0, le=1), py: float = Query(..., ge=0, le=1),
    ox: float = Query(..., ge=0, le=1), oy: float = Query(..., ge=0, le=1),
) -> RingPositionAnalysis:
    """Analyze current ring positions."""
    return _footwork.analyze_position(px, py, ox, oy)


@router.get("/rope-trap", response_model=RopeTracker, summary="Detect rope trap")
async def detect_rope_trap(
    px: float = Query(..., ge=0, le=1), py: float = Query(..., ge=0, le=1),
    ox: float = Query(..., ge=0, le=1), oy: float = Query(..., ge=0, le=1),
    pressure: float = Query(0.5, ge=0, le=1),
) -> RopeTracker:
    """Detect if the player is trapped on the ropes."""
    return _footwork.detect_rope_trap(px, py, ox, oy, pressure)


@router.get("/cutoff-angle", response_model=CutOffAngle, summary="Cut-off angle")
async def calculate_cutoff(
    px: float = Query(..., ge=0, le=1), py: float = Query(..., ge=0, le=1),
    ox: float = Query(..., ge=0, le=1), oy: float = Query(..., ge=0, le=1),
    direction: str = Query("left"),
) -> CutOffAngle:
    """Calculate the optimal angle to cut off an opponent's escape."""
    return _footwork.calculate_cutoff_angle(px, py, ox, oy, direction)


# ---------------------------------------------------------------------------
# ComboEV endpoints
# ---------------------------------------------------------------------------

@router.post("/combo/analyze", response_model=ComboAnalysis, summary="Analyze combo EV")
async def analyze_combo(
    punches: list[PunchType],
    guard: str = Query("high"),
    distance: str = Query("mid"),
) -> ComboAnalysis:
    """Calculate the expected value of a punch combination."""
    return _combo.analyze_combo(punches, guard, distance)


@router.get("/combo/guard-break", response_model=GuardBreakReport, summary="Guard break combos")
async def find_guard_breaks(guard: str = Query("high")) -> GuardBreakReport:
    """Find combos that break through a guard position."""
    return _combo.find_guard_breaks(guard)


@router.get("/combo/jab-economy", response_model=JabEconomyReport, summary="Jab economy")
async def jab_economy(
    thrown: int = Query(..., ge=0), landed: int = Query(..., ge=0),
    total_thrown: int = Query(..., ge=0), rounds: int = Query(1, ge=1),
) -> JabEconomyReport:
    """Analyze jab usage economy."""
    return _combo.analyze_jab_economy(thrown, landed, total_thrown, rounds)


# ---------------------------------------------------------------------------
# JudgeMind endpoints
# ---------------------------------------------------------------------------

@router.post("/score/round", response_model=RoundScore, summary="Score a round")
async def score_round(
    round_num: int = Query(..., ge=1),
    player_stats: dict = ...,
    opponent_stats: dict = ...,
) -> RoundScore:
    """Score a single round using the 10-point must system."""
    try:
        return _judge.score_round(round_num, player_stats, opponent_stats)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/score/projection", response_model=ScorecardProjection, summary="Scorecard projection")
async def project_scorecard(
    round_scores: list[RoundScore],
    total_rounds: int = Query(12, ge=4, le=12),
) -> ScorecardProjection:
    """Project the final scorecard."""
    return _judge.project_scorecard(round_scores, total_rounds)


@router.get("/score/body-roi", response_model=BodyWorkROI, summary="Body work ROI")
async def body_work_roi(
    body_landed: int = Query(..., ge=0),
    body_per_round: float = Query(..., ge=0),
    current_round: int = Query(..., ge=1),
    total_rounds: int = Query(12),
) -> BodyWorkROI:
    """Calculate body work return on investment."""
    return _judge.calculate_body_work_roi(body_landed, body_per_round, current_round, total_rounds)


# ---------------------------------------------------------------------------
# DamageNarrative endpoints
# ---------------------------------------------------------------------------

@router.post("/damage/update/{fight_id}", response_model=DamageState, summary="Update damage")
async def update_damage(
    fight_id: str,
    round_num: int = Query(..., ge=1),
    punches_absorbed: dict = ...,
    knockdowns: int = Query(0, ge=0),
) -> DamageState:
    """Update damage state after a round."""
    try:
        return _damage.update_damage_state(fight_id, round_num, punches_absorbed, knockdowns)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/damage/timeline/{fight_id}", response_model=DamageTimeline, summary="Damage timeline")
async def get_timeline(fight_id: str) -> DamageTimeline:
    """Get full damage timeline for a fight."""
    return _damage.get_damage_timeline(fight_id)


@router.get("/damage/economy", response_model=PunchEconomyReport, summary="Punch economy")
async def punch_economy(
    thrown: int = Query(..., ge=0), landed: int = Query(..., ge=0),
    damage: float = Query(..., ge=0), stamina: float = Query(..., ge=0),
    rounds: int = Query(1, ge=1),
) -> PunchEconomyReport:
    """Analyze punch economy — damage vs stamina investment."""
    return _damage.analyze_punch_economy(thrown, landed, damage, stamina, rounds)
