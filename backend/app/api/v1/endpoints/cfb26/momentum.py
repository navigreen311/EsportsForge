"""API endpoints for CFB 26 MomentumGuard — momentum tracking and exploitation."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.cfb26.momentum import (
    ActionInput,
    GameStateInput,
    MomentumExploit,
    MomentumPrediction,
    MomentumState,
    RecoveryPlan,
)
from app.services.agents.cfb26.momentum_guard import MomentumGuard

router = APIRouter(prefix="/titles/cfb26/momentum", tags=["CFB 26 — Momentum"])

_engine = MomentumGuard()


@router.post("/state", response_model=MomentumState)
async def get_momentum_state(game_state: GameStateInput) -> MomentumState:
    """Calculate the current momentum state from game context."""
    try:
        return _engine.calculate_state(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/predict", response_model=MomentumPrediction)
async def predict_momentum(game_state: GameStateInput) -> MomentumPrediction:
    """Predict upcoming momentum shifts."""
    try:
        return _engine.predict_shift(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/exploit", response_model=MomentumExploit)
async def get_exploit(action: ActionInput) -> MomentumExploit:
    """Get play recommendations to exploit current momentum advantage."""
    try:
        return _engine.get_exploit_actions(action)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/recover", response_model=RecoveryPlan)
async def get_recovery_plan(game_state: GameStateInput) -> RecoveryPlan:
    """Generate a recovery plan when momentum is against the player."""
    try:
        return _engine.generate_recovery_plan(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
