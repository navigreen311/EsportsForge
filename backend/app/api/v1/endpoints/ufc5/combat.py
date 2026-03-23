"""API endpoints for UFC 5 combat intelligence — FightIQ, DamageForge, StaminaChain, GrappleGraph, RoundScore."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.ufc5.combat import (
    ArchetypeStyle,
    BodyRegion,
    CutSeverity,
    DamageState,
    FinishProtocol,
    GrapplePosition,
    GrapplePositionType,
    RoundPlan,
    RoundScore,
    StaminaEconomy,
    StrikeType,
    StyleMatchup,
    SubmissionChain,
    SubmissionType,
    VulnerabilityWindow,
)
from app.services.agents.ufc5.damage_forge import DamageForge
from app.services.agents.ufc5.fight_iq import FightIQ
from app.services.agents.ufc5.grapple_graph import GrappleGraph
from app.services.agents.ufc5.round_score import RoundScoreAI
from app.services.agents.ufc5.stamina_chain import StaminaChain

router = APIRouter(prefix="/titles/ufc5", tags=["UFC 5 — Combat Intelligence"])

_fight_iq = FightIQ()
_grapple_graph = GrappleGraph()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ClassifyOpponentRequest(BaseModel):
    aggression: float = Field(0.5, ge=0.0, le=1.0)
    takedown_rate: float = Field(0.1, ge=0.0, le=1.0)
    clinch_rate: float = Field(0.1, ge=0.0, le=1.0)
    striking_volume: float = Field(0.5, ge=0.0, le=1.0)
    power_ratio: float = Field(0.5, ge=0.0, le=1.0)


class ApplyDamageRequest(BaseModel):
    strike_type: StrikeType
    region: BodyRegion | None = None
    is_critical: bool = False
    round_number: int = Field(1, ge=1, le=5)
    timestamp: float = Field(0.0, ge=0.0)


class RecordStrikeRequest(BaseModel):
    strike: StrikeType
    landed: bool
    is_player: bool = True


class ScoreRoundRequest(BaseModel):
    round_number: int = Field(..., ge=1, le=5)
    sig_strikes_landed: int = Field(0, ge=0)
    sig_strikes_absorbed: int = Field(0, ge=0)
    takedowns_landed: int = Field(0, ge=0)
    takedowns_defended: int = Field(0, ge=0)
    control_time: float = Field(0.0, ge=0.0)
    knockdowns_scored: int = Field(0, ge=0)
    knockdowns_received: int = Field(0, ge=0)


# ---------------------------------------------------------------------------
# FightIQ endpoints
# ---------------------------------------------------------------------------


@router.get("/archetypes", summary="List all fighter archetypes")
async def list_archetypes() -> list[dict[str, str]]:
    """Return all recognized UFC 5 fighter archetypes with descriptions."""
    return _fight_iq.list_archetypes()


@router.post("/classify-opponent", summary="Classify opponent archetype")
async def classify_opponent(body: ClassifyOpponentRequest) -> dict:
    """Classify an opponent into a fighter archetype based on tendencies."""
    archetype = _fight_iq.classify_opponent(body.model_dump())
    return archetype.model_dump()


@router.get(
    "/matchup/{player_style}/{opponent_style}",
    response_model=StyleMatchup,
    summary="Get style matchup card",
)
async def get_matchup(player_style: str, opponent_style: str) -> StyleMatchup:
    """Generate a matchup advantage card between two fighter styles."""
    try:
        ps = ArchetypeStyle(player_style)
        os_ = ArchetypeStyle(opponent_style)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid style: {exc}") from exc
    return _fight_iq.get_matchup_card(ps, os_)


@router.get("/matchups/{player_style}", summary="All matchups for a style")
async def get_all_matchups(player_style: str) -> list[StyleMatchup]:
    """Generate matchup cards against every archetype for the given style."""
    try:
        ps = ArchetypeStyle(player_style)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid style: {exc}") from exc
    return _fight_iq.analyze_all_matchups(ps)


@router.get("/finish-pattern/{archetype}", summary="Finish pattern for archetype")
async def get_finish_pattern(archetype: str) -> dict:
    """Return the typical finish pattern for a given archetype."""
    try:
        a = ArchetypeStyle(archetype)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid archetype: {exc}") from exc
    return _fight_iq.get_finish_pattern(a).model_dump()


# ---------------------------------------------------------------------------
# DamageForge endpoints
# ---------------------------------------------------------------------------


@router.post("/damage/apply", summary="Apply strike damage")
async def apply_damage(body: ApplyDamageRequest) -> dict:
    """Apply a damage event and return the updated damage state."""
    forge = DamageForge()
    entry = forge.apply_damage(
        strike_type=body.strike_type,
        region=body.region,
        is_critical=body.is_critical,
        round_number=body.round_number,
        timestamp=body.timestamp,
    )
    return {
        "entry": entry.model_dump(),
        "state": forge.get_damage_summary(),
    }


@router.get("/damage/vulnerability-windows", summary="Get vulnerability windows")
async def get_vulnerability_windows() -> list[VulnerabilityWindow]:
    """Return all known vulnerability windows from whiffed strikes."""
    forge = DamageForge()
    return forge.get_vulnerability_windows()


# ---------------------------------------------------------------------------
# StaminaChain endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/stamina/economy/{round_number}",
    response_model=StaminaEconomy,
    summary="Get stamina economy for round",
)
async def get_stamina_economy(
    round_number: int,
    total_rounds: int = Query(3, ge=3, le=5),
) -> StaminaEconomy:
    """Generate the stamina economy report for a given round."""
    chain = StaminaChain(total_rounds=total_rounds)
    return chain.get_economy(round_number)


@router.get("/stamina/whiff-model", summary="Whiff punishment model")
async def get_whiff_punishment_model() -> list[dict]:
    """Return the whiff punishment opportunity model."""
    chain = StaminaChain()
    return [p.model_dump() for p in chain.get_whiff_punishment_model()]


# ---------------------------------------------------------------------------
# GrappleGraph endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/grapple/positions",
    summary="All grapple position decision trees",
)
async def get_all_positions() -> list[GrapplePosition]:
    """Return decision trees for all grappling positions."""
    return _grapple_graph.get_all_positions()


@router.get(
    "/grapple/position/{position}",
    response_model=GrapplePosition,
    summary="Decision tree for a position",
)
async def get_position_tree(position: str) -> GrapplePosition:
    """Return the full decision tree for a grapple position."""
    try:
        pos = GrapplePositionType(position)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid position: {exc}") from exc
    return _grapple_graph.get_position_tree(pos)


@router.get(
    "/grapple/submission-chain/{submission}",
    summary="Submission chain from standing",
)
async def get_submission_chain(
    submission: str,
    start: str = Query("standing", description="Starting position"),
) -> SubmissionChain | dict:
    """Build a submission chain from start position to the target submission."""
    try:
        sub = SubmissionType(submission)
        start_pos = GrapplePositionType(start)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid value: {exc}") from exc
    chain = _grapple_graph.get_submission_chain(sub, start_pos)
    if chain is None:
        return {"error": "No valid chain found for this submission from the start position"}
    return chain


@router.get("/grapple/all-chains", summary="All submission chains")
async def get_all_submission_chains(
    start: str = Query("standing", description="Starting position"),
) -> list[SubmissionChain]:
    """Generate chains for all submissions from a starting position."""
    try:
        start_pos = GrapplePositionType(start)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid position: {exc}") from exc
    return _grapple_graph.get_all_submission_chains(start_pos)


# ---------------------------------------------------------------------------
# RoundScore endpoints
# ---------------------------------------------------------------------------


@router.post("/rounds/score", response_model=RoundScore, summary="Score a round")
async def score_round(body: ScoreRoundRequest) -> RoundScore:
    """Score a completed round using the 10-point-must system."""
    ai = RoundScoreAI()
    return ai.score_round(
        round_number=body.round_number,
        sig_strikes_landed=body.sig_strikes_landed,
        sig_strikes_absorbed=body.sig_strikes_absorbed,
        takedowns_landed=body.takedowns_landed,
        takedowns_defended=body.takedowns_defended,
        control_time=body.control_time,
        knockdowns_scored=body.knockdowns_scored,
        knockdowns_received=body.knockdowns_received,
    )


@router.get("/rounds/plan/{round_number}", summary="Generate round plan")
async def generate_round_plan(
    round_number: int,
    total_rounds: int = Query(3, ge=3, le=5),
) -> RoundPlan:
    """Generate a tactical plan for the upcoming round."""
    ai = RoundScoreAI(total_rounds=total_rounds)
    return ai.generate_round_plan(round_number)


@router.get("/rounds/finish-protocol", summary="Build finish protocol")
async def build_finish_protocol() -> FinishProtocol:
    """Build a default finish protocol for when conditions are met."""
    ai = RoundScoreAI()
    return ai.build_finish_protocol()
