"""MomentumGuard schemas — momentum tracking, prediction, exploitation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MomentumDirection(str, Enum):
    """Direction the momentum meter is trending."""

    RISING = "rising"
    FALLING = "falling"
    NEUTRAL = "neutral"
    CRITICAL_HIGH = "critical_high"
    CRITICAL_LOW = "critical_low"


class MomentumTrigger(str, Enum):
    """Events that can shift momentum."""

    TURNOVER = "turnover"
    BIG_PLAY = "big_play"
    SACK = "sack"
    FOURTH_DOWN_STOP = "fourth_down_stop"
    FOURTH_DOWN_CONVERSION = "fourth_down_conversion"
    SCORING_DRIVE = "scoring_drive"
    THREE_AND_OUT = "three_and_out"
    PENALTY = "penalty"
    CROWD_NOISE = "crowd_noise"
    TIMEOUT = "timeout"
    TRICK_PLAY = "trick_play"
    GOAL_LINE_STAND = "goal_line_stand"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class MomentumState(BaseModel):
    """Current momentum meter state."""

    id: UUID = Field(default_factory=uuid4)
    meter_value: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Momentum meter (-1.0=full away, 0=neutral, 1.0=full home).",
    )
    direction: MomentumDirection
    velocity: float = Field(
        default=0.0,
        description="Rate of momentum change per play.",
    )
    home_team: str = Field(default="")
    away_team: str = Field(default="")
    quarter: int = Field(default=1, ge=1, le=5)
    game_clock: str = Field(default="15:00")
    recent_triggers: list[MomentumTrigger] = Field(default_factory=list)
    plays_since_last_shift: int = Field(default=0, ge=0)
    measured_at: datetime = Field(default_factory=datetime.utcnow)


class MomentumPrediction(BaseModel):
    """Prediction of how an action will affect momentum."""

    predicted_shift: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Predicted change to momentum meter value.",
    )
    new_meter_value: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Predicted meter value after action.",
    )
    new_direction: MomentumDirection
    trigger_probability: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Probability this action triggers a momentum event.",
    )
    risk_level: str = Field(
        default="medium",
        description="Risk level: low, medium, high, critical.",
    )
    reasoning: str = Field(
        default="",
        description="Why this prediction was made.",
    )


class MomentumExploit(BaseModel):
    """How to exploit the current momentum state."""

    strategy: str = Field(
        ..., description="High-level exploitation strategy.",
    )
    recommended_plays: list[str] = Field(
        default_factory=list,
        description="Play types that benefit from current momentum.",
    )
    tempo_recommendation: str = Field(
        default="normal",
        description="Recommended tempo: hurry_up, normal, slow_down, milk_clock.",
    )
    aggression_level: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How aggressive to be (0=conservative, 1=all-out).",
    )
    key_advantages: list[str] = Field(
        default_factory=list,
        description="Specific advantages from current momentum.",
    )
    window_plays: int = Field(
        default=5, ge=1,
        description="Estimated plays before momentum window closes.",
    )


class RecoveryPlan(BaseModel):
    """Plan to recover from a momentum deficit."""

    severity: str = Field(
        ..., description="How bad the deficit is: mild, moderate, severe, dire.",
    )
    immediate_actions: list[str] = Field(
        default_factory=list,
        description="Things to do right now.",
    )
    play_style_shift: str = Field(
        default="",
        description="How to shift play style to stop the bleeding.",
    )
    timeout_recommendation: bool = Field(
        default=False,
        description="Whether to call a timeout to break momentum.",
    )
    estimated_plays_to_neutral: int = Field(
        default=5, ge=1,
        description="Estimated plays to get back to neutral.",
    )
    risk_acceptance: str = Field(
        default="",
        description="What risks are worth taking in this state.",
    )


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class GameStateInput(BaseModel):
    """Input representing current game state for momentum tracking."""

    home_team: str
    away_team: str
    home_score: int = Field(default=0, ge=0)
    away_score: int = Field(default=0, ge=0)
    quarter: int = Field(default=1, ge=1, le=5)
    game_clock: str = Field(default="15:00")
    possession: str = Field(default="home", description="'home' or 'away'.")
    down: int = Field(default=1, ge=1, le=4)
    distance: int = Field(default=10, ge=0)
    field_position: int = Field(
        default=25, ge=0, le=100,
        description="Yard line from own goal (0=own goal, 100=opponent goal).",
    )
    is_home_game: bool = Field(default=True)
    stadium_noise_level: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Current crowd noise intensity.",
    )
    recent_events: list[str] = Field(
        default_factory=list,
        description="Recent game events for momentum context.",
    )


class ActionInput(BaseModel):
    """Input describing a planned action for momentum prediction."""

    action_type: str = Field(
        ..., description="e.g. 'deep_pass', 'run_play', 'trick_play', 'timeout'.",
    )
    aggression: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How aggressive the action is.",
    )
    context: dict = Field(
        default_factory=dict,
        description="Additional context about the action.",
    )


class MomentumResponse(BaseModel):
    """Envelope for momentum endpoints."""

    game_id: str = Field(default="")
    state: MomentumState
    exploit: MomentumExploit | None = None
    prediction: MomentumPrediction | None = None
