"""API endpoints for PlayerTwin — the player personalization engine."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.player_twin import (
    BenchmarkComparison,
    BootstrapRequest,
    CanExecuteResponse,
    ExecutionScore,
    PanicPattern,
    PlayerIdentity,
    PlayerTwinProfile,
    PressureDifferential,
    RecommendationInput,
    TendencyMap,
    TransferRate,
    GameMode,
)
from app.services.backbone import execution_engine, identity_engine, player_twin

router = APIRouter(prefix="/player-twin", tags=["PlayerTwin"])


# ── Full profile ──────────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=PlayerTwinProfile)
async def get_player_profile(
    user_id: str,
    title: str = Query(..., description="Game title, e.g. 'madden26'"),
):
    """Return the full PlayerTwin digital model for a user + title."""
    return player_twin.get_profile(user_id, title)


# ── Execution ─────────────────────────────────────────────────────────────

@router.get("/{user_id}/execution", response_model=list[ExecutionScore])
async def get_execution_scores(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """All execution ceiling scores for this player in a title."""
    return execution_engine.get_all_scores(user_id, title)


@router.get("/{user_id}/execution/{skill}", response_model=ExecutionScore)
async def get_execution_skill(
    user_id: str,
    skill: str,
    title: str = Query(..., description="Game title"),
):
    """Execution ceiling for a single skill dimension."""
    return execution_engine.score_execution(user_id, title, skill)


@router.get("/{user_id}/execution/pressure-differential", response_model=PressureDifferential)
async def get_pressure_differential(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Normal vs pressure execution gap."""
    return execution_engine.get_pressure_differential(user_id, title)


@router.get("/{user_id}/execution/transfer-rate", response_model=TransferRate)
async def get_transfer_rate(
    user_id: str,
    skill: str = Query(..., description="Skill dimension"),
    from_mode: GameMode = Query(..., description="Source game mode"),
    to_mode: GameMode = Query(..., description="Target game mode"),
):
    """How well a skill transfers between game modes (e.g. lab -> ranked)."""
    return execution_engine.get_transfer_rate(user_id, skill, from_mode, to_mode)


# ── Identity ──────────────────────────────────────────────────────────────

@router.get("/{user_id}/identity", response_model=PlayerIdentity)
async def get_identity(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Player identity / philosophy profile."""
    return identity_engine.get_identity(user_id, title)


# ── Tendencies & panic ────────────────────────────────────────────────────

@router.get("/{user_id}/tendencies", response_model=TendencyMap)
async def get_tendencies(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Play style tendencies for a title."""
    return player_twin.get_tendencies(user_id, title)


@router.get("/{user_id}/panic-patterns", response_model=list[PanicPattern])
async def get_panic_patterns(
    user_id: str,
    title: str = Query(..., description="Game title"),
):
    """Recurring failure patterns under pressure."""
    return player_twin.get_panic_patterns(user_id, title)


# ── Benchmark ─────────────────────────────────────────────────────────────

@router.get("/{user_id}/benchmark", response_model=BenchmarkComparison)
async def get_benchmark(
    user_id: str,
    title: str = Query(..., description="Game title"),
    percentile: int = Query(50, ge=0, le=100, description="Target percentile to compare against"),
):
    """Compare player to a population percentile."""
    return player_twin.compare_to_benchmark(user_id, title, percentile)


# ── Can-execute ───────────────────────────────────────────────────────────

@router.post("/{user_id}/can-execute", response_model=CanExecuteResponse)
async def can_execute(
    user_id: str,
    recommendation: RecommendationInput,
):
    """Evaluate whether the player can reliably execute a recommendation."""
    return player_twin.can_execute(user_id, recommendation)


# ── Bootstrap (onboarding) ───────────────────────────────────────────────

@router.post("/{user_id}/bootstrap", response_model=PlayerTwinProfile)
async def bootstrap_profile(
    user_id: str,
    body: BootstrapRequest,
):
    """Initialize a PlayerTwin profile from the first N game sessions."""
    if not body.sessions:
        raise HTTPException(status_code=400, detail="At least one session is required")
    return player_twin.bootstrap_from_sessions(user_id, body.sessions)
