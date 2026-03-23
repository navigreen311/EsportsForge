"""Pydantic schemas for SimLab AI and Dynamic Calibration Engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ScenarioType(str, Enum):
    """Classification of simulation scenarios."""
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    SPECIAL_TEAMS = "special_teams"
    CLUTCH = "clutch"
    TWO_MINUTE = "two_minute"
    CUSTOM = "custom"


class CalibrationLevel(str, Enum):
    """Difficulty tier for the calibration engine."""
    BEGINNER = "beginner"
    DEVELOPING = "developing"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ELITE = "elite"
    MASTER = "master"


class CalibrationDirection(str, Enum):
    """Which way the calibration moved after a rep."""
    UP = "up"
    DOWN = "down"
    HOLD = "hold"


# ---------------------------------------------------------------------------
# Game State & Scenario
# ---------------------------------------------------------------------------

class GameState(BaseModel):
    """Snapshot of the game at a single point in time."""
    title: str = Field(..., description="Game title, e.g. 'madden26'")
    quarter: int = Field(1, ge=1, le=4, description="Current quarter")
    time_remaining: float = Field(900.0, ge=0, description="Seconds left in quarter")
    score_home: int = Field(0, ge=0)
    score_away: int = Field(0, ge=0)
    possession: str = Field("home", description="'home' or 'away'")
    down: int | None = Field(None, ge=1, le=4)
    yards_to_go: int | None = Field(None, ge=0)
    field_position: int | None = Field(None, ge=0, le=100, description="Yard line 0-100")
    custom_vars: dict[str, Any] = Field(default_factory=dict, description="Title-specific state")


class Scenario(BaseModel):
    """A what-if scenario built from a game state plus a modifier."""
    id: str = Field(..., description="Unique scenario identifier")
    name: str = Field("", description="Human-readable label")
    scenario_type: ScenarioType = Field(ScenarioType.CUSTOM)
    base_state: GameState
    what_if: str = Field("", description="Natural-language what-if modifier")
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Decision Tree
# ---------------------------------------------------------------------------

class DecisionNode(BaseModel):
    """Single node in a decision tree."""
    id: str
    label: str = Field(..., description="Action or condition description")
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    risk: float = Field(0.0, ge=0.0, le=1.0, description="Risk factor 0-1")
    children: list[DecisionNode] = Field(default_factory=list)

    class Config:
        # Allow recursive model
        arbitrary_types_allowed = True


class DecisionTree(BaseModel):
    """Full decision tree for a simulated scenario."""
    scenario_id: str
    root: DecisionNode
    depth: int = Field(3, ge=1)
    best_path: list[str] = Field(default_factory=list, description="IDs of best-path nodes")


# ---------------------------------------------------------------------------
# Simulation Results
# ---------------------------------------------------------------------------

class SimulationResult(BaseModel):
    """Output of a simulation run."""
    scenario_id: str
    decision_tree: DecisionTree
    best_response: str = Field("", description="Recommended action summary")
    win_probability: float = Field(0.5, ge=0.0, le=1.0)
    risk_assessment: float = Field(0.0, ge=0.0, le=1.0)
    analysis: str = Field("", description="Natural-language breakdown")
    timestamp: datetime | None = None


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

class CalibrationConfig(BaseModel):
    """Persistent calibration state for a user + skill pair."""
    user_id: str
    skill: str
    level: CalibrationLevel = Field(CalibrationLevel.INTERMEDIATE)
    difficulty_value: float = Field(0.5, ge=0.0, le=1.0, description="Continuous difficulty 0-1")
    target_success_rate: float = Field(0.70, ge=0.0, le=1.0)
    current_success_rate: float = Field(0.0, ge=0.0, le=1.0)
    reps_at_level: int = Field(0, ge=0)
    total_reps: int = Field(0, ge=0)
    streak_successes: int = Field(0, ge=0)
    streak_failures: int = Field(0, ge=0)
    updated_at: datetime | None = None


class DifficultyAdjustment(BaseModel):
    """Result of a single calibration adjustment."""
    user_id: str
    skill: str
    previous_difficulty: float = Field(..., ge=0.0, le=1.0)
    new_difficulty: float = Field(..., ge=0.0, le=1.0)
    previous_level: CalibrationLevel
    new_level: CalibrationLevel
    direction: CalibrationDirection
    reason: str = Field("", description="Why the adjustment was made")


# ---------------------------------------------------------------------------
# Request / Response helpers
# ---------------------------------------------------------------------------

class SimRequest(BaseModel):
    """Request body for creating or running a simulation."""
    game_state: GameState
    what_if: str = Field("", description="Natural-language what-if modifier")
    name: str = Field("", description="Optional scenario name")
    scenario_type: ScenarioType = Field(ScenarioType.CUSTOM)
    depth: int = Field(3, ge=1, le=6, description="Decision tree depth")


class CalibrationRequest(BaseModel):
    """Request body for a calibration adjustment after a rep."""
    user_id: str
    skill: str
    success: bool = Field(..., description="Whether the rep was successful")
