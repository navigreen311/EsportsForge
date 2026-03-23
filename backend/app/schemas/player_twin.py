"""Pydantic schemas for the PlayerTwin personalization engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PressureLevel(str, Enum):
    """Contextual pressure classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CLUTCH = "clutch"  # final minute / elimination scenarios


class PlayStyle(str, Enum):
    """Archetype labels derived from observed behavior."""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"
    CHAOTIC = "chaotic"


class GameMode(str, Enum):
    """Mode context for transfer-rate calculations."""
    LAB = "lab"           # practice / training mode
    CASUAL = "casual"
    RANKED = "ranked"
    TOURNAMENT = "tournament"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class ExecutionScore(BaseModel):
    """Reliability score for a single skill dimension."""
    skill: str = Field(..., description="Skill dimension name, e.g. 'user_blitz', 'zone_read'")
    title: str = Field(..., description="Game title, e.g. 'madden26'")
    score: float = Field(..., ge=0.0, le=1.0, description="0-1 reliability rating")
    sample_size: int = Field(0, ge=0, description="Number of observations")
    pressure_score: float = Field(0.0, ge=0.0, le=1.0, description="Score under pressure specifically")
    trend: float = Field(0.0, description="Recent trend direction: positive = improving")
    last_updated: datetime | None = None


class PanicPattern(BaseModel):
    """Describes a recurring failure mode under pressure."""
    pattern_id: str = Field(..., description="Unique slug, e.g. 'early_timeout_call'")
    title: str
    description: str
    trigger: str = Field(..., description="What situation triggers this pattern")
    frequency: float = Field(0.0, ge=0.0, le=1.0, description="How often it occurs when triggered")
    severity: float = Field(0.0, ge=0.0, le=1.0, description="Impact on game outcome")
    counter_strategy: str | None = Field(None, description="Suggested mitigation")
    last_observed: datetime | None = None


class TendencyEntry(BaseModel):
    """Single tendency observation."""
    category: str = Field(..., description="e.g. 'play_calling', 'clock_management'")
    tendency: str = Field(..., description="e.g. 'favors_run_on_3rd_and_short'")
    weight: float = Field(0.0, ge=0.0, le=1.0, description="Strength of this tendency")
    context: str | None = Field(None, description="Situational context")


class TendencyMap(BaseModel):
    """Aggregated tendencies for a player in a specific title."""
    title: str
    entries: list[TendencyEntry] = Field(default_factory=list)
    dominant_style: PlayStyle = PlayStyle.BALANCED
    last_updated: datetime | None = None


class BenchmarkComparison(BaseModel):
    """How a player compares to a population percentile."""
    title: str
    target_percentile: int = Field(..., ge=0, le=100)
    dimensions: dict[str, float] = Field(
        default_factory=dict,
        description="Skill dimension -> player's percentile in that dimension",
    )
    overall_percentile: float = Field(0.0, ge=0.0, le=100.0)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class TransferRate(BaseModel):
    """How well execution transfers across game modes."""
    skill: str
    from_mode: GameMode
    to_mode: GameMode
    rate: float = Field(0.0, ge=0.0, le=1.0, description="1.0 = perfect transfer")
    sample_size: int = 0


class PressureDifferential(BaseModel):
    """Gap between normal and pressure execution."""
    title: str
    normal_avg: float = Field(0.0, ge=0.0, le=1.0)
    pressure_avg: float = Field(0.0, ge=0.0, le=1.0)
    differential: float = Field(0.0, description="Negative = worse under pressure")
    clutch_rating: float = Field(0.0, ge=0.0, le=1.0, description="Composite clutch score")


# ---------------------------------------------------------------------------
# Identity (personal philosophy layer)
# ---------------------------------------------------------------------------

class PlayerIdentity(BaseModel):
    """Player's strategic DNA — how they *want* to play."""
    user_id: str
    title: str
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0, description="0=very conservative, 1=max risk")
    aggression: float = Field(0.5, ge=0.0, le=1.0)
    pace: float = Field(0.5, ge=0.0, le=1.0, description="0=slow/methodical, 1=uptempo")
    creativity: float = Field(0.5, ge=0.0, le=1.0, description="0=meta-only, 1=off-meta innovator")
    adaptability: float = Field(0.5, ge=0.0, le=1.0, description="How quickly they adjust mid-game")
    style: PlayStyle = PlayStyle.BALANCED
    stated_vs_actual_gap: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Divergence between what they say and what they do",
    )
    last_updated: datetime | None = None


# ---------------------------------------------------------------------------
# Top-level profile
# ---------------------------------------------------------------------------

class PlayerTwinProfile(BaseModel):
    """Complete digital model of a player for a specific title."""
    user_id: str
    title: str
    identity: PlayerIdentity
    execution_scores: list[ExecutionScore] = Field(default_factory=list)
    panic_patterns: list[PanicPattern] = Field(default_factory=list)
    tendencies: TendencyMap
    benchmark: BenchmarkComparison | None = None
    sessions_analyzed: int = 0
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Overall profile confidence — rises with more sessions",
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Request / response helpers
# ---------------------------------------------------------------------------

class SessionData(BaseModel):
    """Incoming session payload from LoopAI."""
    session_id: str
    user_id: str
    title: str
    mode: GameMode = GameMode.RANKED
    result: str = Field(..., description="win / loss / draw")
    score_differential: int = 0
    duration_seconds: int = 0
    plays: list[dict[str, Any]] = Field(default_factory=list)
    pressure_moments: list[dict[str, Any]] = Field(default_factory=list)
    skill_events: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime | None = None


class BootstrapRequest(BaseModel):
    """Payload for initial profile creation from first N sessions."""
    sessions: list[SessionData] = Field(..., min_length=1)


class RecommendationInput(BaseModel):
    """A recommendation to evaluate against player capability."""
    action: str
    required_skills: list[str] = Field(default_factory=list)
    difficulty: float = Field(0.5, ge=0.0, le=1.0)
    pressure_context: PressureLevel = PressureLevel.MEDIUM


class CanExecuteResponse(BaseModel):
    """Whether the player can reliably execute a recommendation."""
    can_execute: bool
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    limiting_skills: list[str] = Field(default_factory=list)
    suggestion: str | None = None
