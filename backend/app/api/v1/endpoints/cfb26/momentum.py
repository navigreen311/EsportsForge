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


class PredictRequest(GameStateInput):
    """Body for /predict — needs both the current game state and the action being scored."""
    action: ActionInput


@router.post("/state", response_model=MomentumState)
async def get_momentum_state(game_state: GameStateInput) -> MomentumState:
    """Calculate the current momentum state from game context."""
    try:
        return _engine.track_momentum(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/predict", response_model=MomentumPrediction)
async def predict_momentum(payload: PredictRequest) -> MomentumPrediction:
    """Predict the momentum shift from a candidate action given current game state."""
    try:
        action = payload.action
        # Reconstruct game_state from the wrapper without the action field
        game_state = GameStateInput(**{k: v for k, v in payload.model_dump().items() if k != "action"})
        return _engine.predict_momentum_shift(game_state, action)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/exploit", response_model=MomentumExploit)
async def get_exploit(game_state: GameStateInput) -> MomentumExploit:
    """Get play recommendations to exploit current momentum advantage."""
    try:
        state = _engine.track_momentum(game_state)
        return _engine.get_momentum_exploit(state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/recover", response_model=RecoveryPlan)
async def get_recovery_plan(game_state: GameStateInput) -> RecoveryPlan:
    """Generate a recovery plan when momentum is against the player."""
    try:
        state = _engine.track_momentum(game_state)
        return _engine.get_momentum_recovery(state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
