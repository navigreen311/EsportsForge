"""API endpoints for ClockAI — clock management intelligence."""

from fastapi import APIRouter, HTTPException

from app.schemas.madden26.clock import (
    ClockDecision,
    EndGamePlan,
    FourthDownDecision,
    GameState,
    SimulationRequest,
    SimulationResult,
    TimeoutAdvice,
    TwoMinutePlan,
)
from app.services.agents.madden26.clock_ai import ClockAI

router = APIRouter(prefix="/titles/madden26/clock", tags=["Madden 26 — ClockAI"])

_clock_ai = ClockAI()


@router.post("/decision", response_model=ClockDecision)
async def clock_decision(game_state: GameState) -> ClockDecision:
    """Get the optimal clock management decision for the current game state."""
    try:
        return _clock_ai.get_clock_decision(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/two-minute", response_model=TwoMinutePlan)
async def two_minute_drill(game_state: GameState) -> TwoMinutePlan:
    """Generate a full 2-minute drill play call sequence."""
    try:
        return _clock_ai.two_minute_drill(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/fourth-down", response_model=FourthDownDecision)
async def fourth_down(game_state: GameState) -> FourthDownDecision:
    """Get 4th down recommendation: go for it, punt, or field goal."""
    try:
        return _clock_ai.fourth_down_decision(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/end-game", response_model=EndGamePlan)
async def end_game_scenario(game_state: GameState) -> EndGamePlan:
    """Generate an end-game management plan."""
    try:
        return _clock_ai.end_game_scenario(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/timeout", response_model=TimeoutAdvice)
async def timeout_advice(game_state: GameState) -> TimeoutAdvice:
    """Evaluate whether to use a timeout right now."""
    try:
        return _clock_ai.evaluate_timeout_usage(game_state)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/simulate", response_model=SimulationResult)
async def simulate_scenario(request: SimulationRequest) -> SimulationResult:
    """Run a what-if scenario simulation with a play sequence."""
    try:
        return _clock_ai.simulate_scenario(request.initial_state, request.plays)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
