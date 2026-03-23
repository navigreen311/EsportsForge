"""Pydantic schemas for BankrollForge — bankroll management and variance modeling."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.video_poker.strategy import VariantType


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    """Bankroll risk tolerance."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


# ---------------------------------------------------------------------------
# Core Models
# ---------------------------------------------------------------------------

class SessionBudget(BaseModel):
    """Calculated session bankroll with limits."""
    session_bankroll: float = Field(..., ge=0.0)
    bet_size: float
    total_bankroll: float
    hands_supported: int = Field(..., ge=0)
    estimated_duration_hours: float = Field(..., ge=0.0)
    stop_loss: float = Field(..., ge=0.0)
    win_goal: float = Field(..., ge=0.0)
    risk_level: RiskLevel
    warning: str | None = None


class StopLossConfig(BaseModel):
    """Stop-loss and win-goal configuration."""
    session_bankroll: float
    stop_loss_pct: float
    stop_loss_amount: float
    win_goal_pct: float
    win_goal_amount: float
    trailing_stop_enabled: bool
    walk_away_floor: float
    walk_away_ceiling: float
    rules: list[str]


class WinGoalStatus(BaseModel):
    """Current session status vs. stop-loss/win-goal."""
    action: str = Field(..., description="continue | lock_profit | stop")
    reason: str
    current_balance: float
    net_result: float
    message: str
    pct_of_stop_loss: float
    pct_of_win_goal: float


class VarianceProfile(BaseModel):
    """Variance modeling for a session."""
    variant: VariantType
    bet_size: float
    num_hands: int
    sd_per_hand: float
    session_sd_dollars: float
    expected_loss_dollars: float
    ci_68_range: tuple[float, float]
    ci_95_range: tuple[float, float]
    prob_ahead_pct: float
    risk_assessment: str


class RuinProbability(BaseModel):
    """Probability of losing entire bankroll."""
    ruin_pct: float = Field(..., ge=0.0, le=100.0)
    bankroll: float
    bet_size: float
    target_hands: int
    bankroll_to_bet_ratio: float
    assessment: str


class BankrollPlan(BaseModel):
    """Comprehensive bankroll management plan."""
    total_bankroll: float
    recommended_bet_size: float
    session_bankroll: float
    sessions_per_week: int
    weekly_exposure: float
    weekly_expected_cost: float
    ruin_probability_pct: float
    risk_level: RiskLevel
    variant: VariantType
    rules: list[str]


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class SessionBudgetRequest(BaseModel):
    """Request for session bankroll calculation."""
    total_bankroll: float = Field(..., gt=0)
    bet_size: float = Field(..., gt=0)
    variant: VariantType = VariantType.JACKS_OR_BETTER
    risk_level: RiskLevel = RiskLevel.MODERATE
    target_hours: float = Field(2.0, gt=0, le=4.0)


class SessionBudgetResponse(BaseModel):
    """Response with session budget."""
    budget: SessionBudget


class StopLossConfigRequest(BaseModel):
    """Request to configure stop-loss."""
    session_bankroll: float = Field(..., gt=0)
    stop_loss_pct: float = Field(40.0, gt=0, le=100)
    win_goal_pct: float = Field(30.0, gt=0, le=500)
    trailing_stop: bool = False


class StopLossConfigResponse(BaseModel):
    """Response with stop-loss config."""
    config: StopLossConfig


class WinGoalCheckRequest(BaseModel):
    """Request to check win-goal status."""
    session_bankroll: float = Field(..., gt=0)
    current_balance: float
    stop_loss_config: StopLossConfig
    peak_balance: float | None = None


class WinGoalCheckResponse(BaseModel):
    """Response with win-goal status."""
    status: WinGoalStatus


class VarianceModelRequest(BaseModel):
    """Request for variance modeling."""
    variant: VariantType = VariantType.JACKS_OR_BETTER
    bet_size: float = Field(1.25, gt=0)
    num_hands: int = Field(1000, gt=0, le=100000)


class VarianceModelResponse(BaseModel):
    """Response with variance profile."""
    profile: VarianceProfile


class BankrollPlanRequest(BaseModel):
    """Request for bankroll plan creation."""
    total_bankroll: float = Field(..., gt=0)
    variant: VariantType = VariantType.JACKS_OR_BETTER
    risk_level: RiskLevel = RiskLevel.MODERATE
    sessions_per_week: int = Field(3, gt=0, le=7)


class BankrollPlanResponse(BaseModel):
    """Response with bankroll plan."""
    plan: BankrollPlan
