"""Schemas for ClockAI — 2-minute drill, 4th down, end-game scenario management."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ClockAction(str, Enum):
    """High-level clock action recommendation."""
    HURRY_UP = "hurry_up"
    MILK_CLOCK = "milk_clock"
    SPIKE = "spike"
    CALL_TIMEOUT = "call_timeout"
    NORMAL = "normal"
    KNEEL = "kneel"


class FourthDownChoice(str, Enum):
    """Fourth-down decision options."""
    GO_FOR_IT = "go_for_it"
    PUNT = "punt"
    FIELD_GOAL = "field_goal"


class PlayType(str, Enum):
    """Play classification."""
    RUN = "run"
    PASS_SHORT = "pass_short"
    PASS_MEDIUM = "pass_medium"
    PASS_DEEP = "pass_deep"
    SCREEN = "screen"
    DRAW = "draw"
    QB_SNEAK = "qb_sneak"
    SPIKE = "spike"
    KNEEL = "kneel"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class GameState(BaseModel):
    """Snapshot of current game state for clock decisions."""
    quarter: int = Field(..., ge=1, le=4, description="Current quarter (1-4)")
    time_remaining_seconds: int = Field(..., ge=0, description="Seconds left in quarter")
    score_user: int = Field(..., ge=0, description="User's current score")
    score_opponent: int = Field(..., ge=0, description="Opponent's current score")
    down: int = Field(..., ge=1, le=4, description="Current down")
    yards_to_go: int = Field(..., ge=1, description="Yards needed for first down")
    yard_line: int = Field(..., ge=1, le=99, description="Field position (1=own goal, 99=opp goal)")
    timeouts_user: int = Field(3, ge=0, le=3, description="User timeouts remaining")
    timeouts_opponent: int = Field(3, ge=0, le=3, description="Opponent timeouts remaining")
    is_user_possession: bool = Field(True, description="True if user has the ball")
    is_two_minute_warning_used: bool = Field(False)


class SimulationRequest(BaseModel):
    """Request payload for scenario simulation."""
    initial_state: GameState
    plays: list[str] = Field(..., min_length=1, max_length=20, description="Sequence of play names to simulate")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ClockDecision(BaseModel):
    """What to do with the clock right now."""
    action: ClockAction
    reasoning: str = Field(..., description="Why this action is optimal")
    urgency: float = Field(..., ge=0.0, le=1.0, description="0=no rush, 1=critical")
    recommended_play_type: PlayType | None = None
    seconds_burned_estimate: float = Field(0.0, ge=0.0)


class PlayCall(BaseModel):
    """A single play call inside a drill plan."""
    play_name: str
    play_type: PlayType
    clock_action: ClockAction
    target_yards: int
    rationale: str


class TwoMinutePlan(BaseModel):
    """Full 2-minute drill call sequence."""
    game_state_snapshot: GameState
    total_plays_planned: int
    estimated_score_probability: float = Field(..., ge=0.0, le=1.0)
    play_sequence: list[PlayCall]
    notes: str = ""


class FourthDownDecision(BaseModel):
    """Go / punt / FG recommendation with probabilities."""
    recommendation: FourthDownChoice
    go_probability: float = Field(..., ge=0.0, le=1.0)
    punt_value: float = Field(..., description="Expected point differential if punting")
    fg_probability: float | None = Field(None, ge=0.0, le=1.0, description="FG make probability if in range")
    reasoning: str
    break_even_yards: float = Field(..., description="Yards-to-go where go/punt breaks even")


class EndGamePlan(BaseModel):
    """End-game management plan."""
    scenario_label: str = Field(..., description="e.g. 'trailing by 7, 1:30 left'")
    win_probability: float = Field(..., ge=0.0, le=1.0)
    strategy: str
    play_sequence: list[PlayCall]
    critical_moments: list[str] = Field(default_factory=list, description="Key decision points")


class TimeoutAdvice(BaseModel):
    """When and why to use timeouts."""
    should_use_timeout: bool
    reasoning: str
    optimal_time_to_use: int | None = Field(None, description="Seconds on clock when timeout is optimal")
    timeouts_after: int = Field(..., ge=0, le=3)


class PlayOutcome(BaseModel):
    """Simulated outcome for a single play."""
    play_name: str
    yards_gained: int
    time_elapsed_seconds: int
    new_down: int
    new_yards_to_go: int
    new_yard_line: int
    turnover: bool = False
    score_change: int = 0


class SimulationResult(BaseModel):
    """What-if scenario testing result."""
    initial_state: GameState
    play_outcomes: list[PlayOutcome]
    final_score_user: int
    final_score_opponent: int
    final_time_remaining: int
    win_probability: float = Field(..., ge=0.0, le=1.0)
    summary: str
