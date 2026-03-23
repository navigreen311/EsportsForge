"""API endpoints for BankrollForge — bankroll management and variance modeling."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.video_poker.bankroll import (
    BankrollPlanRequest,
    BankrollPlanResponse,
    SessionBudgetRequest,
    SessionBudgetResponse,
    StopLossConfigRequest,
    StopLossConfigResponse,
    VarianceModelRequest,
    VarianceModelResponse,
    WinGoalCheckRequest,
    WinGoalCheckResponse,
)
from app.services.agents.video_poker.bankroll_forge import BankrollForge

router = APIRouter(
    prefix="/titles/video-poker/bankroll",
    tags=["Video Poker — Bankroll"],
)

_bankroll_forge = BankrollForge()


# --------------------------------------------------------------------------
# POST /titles/video-poker/bankroll/session-budget
# --------------------------------------------------------------------------

@router.post("/session-budget", response_model=SessionBudgetResponse)
async def calculate_session_budget(
    request: SessionBudgetRequest,
) -> SessionBudgetResponse:
    """Calculate optimal session bankroll based on total funds and risk tolerance."""
    try:
        budget = _bankroll_forge.calculate_session_bankroll(
            request.total_bankroll,
            request.bet_size,
            request.variant,
            request.risk_level,
            request.target_hours,
        )
        return SessionBudgetResponse(budget=budget)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/bankroll/stop-loss-config
# --------------------------------------------------------------------------

@router.post("/stop-loss-config", response_model=StopLossConfigResponse)
async def configure_stop_loss(
    request: StopLossConfigRequest,
) -> StopLossConfigResponse:
    """Configure stop-loss and win-goal discipline."""
    try:
        config = _bankroll_forge.configure_stop_loss(
            request.session_bankroll,
            request.stop_loss_pct,
            request.win_goal_pct,
            request.trailing_stop,
        )
        return StopLossConfigResponse(config=config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/bankroll/check-win-goal
# --------------------------------------------------------------------------

@router.post("/check-win-goal", response_model=WinGoalCheckResponse)
async def check_win_goal(request: WinGoalCheckRequest) -> WinGoalCheckResponse:
    """Check current session status against stop-loss and win-goal."""
    try:
        status = _bankroll_forge.check_win_goal(
            request.session_bankroll,
            request.current_balance,
            request.stop_loss_config,
            request.peak_balance,
        )
        return WinGoalCheckResponse(status=status)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/bankroll/variance-model
# --------------------------------------------------------------------------

@router.post("/variance-model", response_model=VarianceModelResponse)
async def model_variance(request: VarianceModelRequest) -> VarianceModelResponse:
    """Model expected variance over a number of hands."""
    try:
        profile = _bankroll_forge.model_variance(
            request.variant, request.bet_size, request.num_hands,
        )
        return VarianceModelResponse(profile=profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# --------------------------------------------------------------------------
# POST /titles/video-poker/bankroll/plan
# --------------------------------------------------------------------------

@router.post("/plan", response_model=BankrollPlanResponse)
async def create_bankroll_plan(
    request: BankrollPlanRequest,
) -> BankrollPlanResponse:
    """Create a comprehensive bankroll management plan."""
    try:
        plan = _bankroll_forge.create_bankroll_plan(
            request.total_bankroll,
            request.variant,
            request.risk_level,
            request.sessions_per_week,
        )
        return BankrollPlanResponse(plan=plan)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
