"""API endpoints for PokerStrategyAI — optimal play and mistake analysis."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.video_poker.strategy import (
    MistakeCheckRequest,
    MistakeCheckResponse,
    OptimalHoldRequest,
    OptimalHoldResponse,
    SessionAnalysisRequest,
    SessionAnalysisResponse,
)
from app.services.agents.video_poker.poker_strategy import PokerStrategyAI

router = APIRouter(
    prefix="/titles/video-poker/strategy",
    tags=["Video Poker — Strategy"],
)

_strategy_ai = PokerStrategyAI()


# --------------------------------------------------------------------------
# POST /titles/video-poker/strategy/optimal-hold
# --------------------------------------------------------------------------

@router.post("/optimal-hold", response_model=OptimalHoldResponse)
async def get_optimal_hold(request: OptimalHoldRequest) -> OptimalHoldResponse:
    """Get the mathematically optimal hold decision for a dealt hand."""
    try:
        decision = _strategy_ai.get_optimal_hold(request.hand, request.variant)
        pay_table = _strategy_ai.get_pay_table(request.variant)
        return OptimalHoldResponse(
            decision=decision,
            variant=request.variant,
            pay_table={k.value: v for k, v in pay_table.items()},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/strategy/check-mistake
# --------------------------------------------------------------------------

@router.post("/check-mistake", response_model=MistakeCheckResponse)
async def check_mistake(request: MistakeCheckRequest) -> MistakeCheckResponse:
    """Check if a player's hold decision was optimal."""
    try:
        classification = _strategy_ai.classify_mistake(
            request.hand, request.player_holds, request.variant,
        )
        return MistakeCheckResponse(classification=classification)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/strategy/session-analysis
# --------------------------------------------------------------------------

@router.post("/session-analysis", response_model=SessionAnalysisResponse)
async def analyze_session(request: SessionAnalysisRequest) -> SessionAnalysisResponse:
    """Analyze a full session of hands for strategy quality."""
    try:
        analysis = _strategy_ai.analyze_session(request.decisions, request.variant)
        return SessionAnalysisResponse(analysis=analysis)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
