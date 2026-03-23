"""Pydantic schemas for Mental services — confidence, benchmarks, narrative."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MomentumDirection(str, Enum):
    """Current momentum trend."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class MilestoneCategory(str, Enum):
    """Types of player milestones."""
    STREAK = "streak"
    PERCENTILE = "percentile"
    SKILL = "skill"
    CONSISTENCY = "consistency"
    IMPROVEMENT = "improvement"


class ReadinessLevel(str, Enum):
    """Pre-game readiness classification."""
    PEAK = "peak"
    READY = "ready"
    MODERATE = "moderate"
    FATIGUED = "fatigued"
    LOW = "low"


# ---------------------------------------------------------------------------
# Confidence & Momentum
# ---------------------------------------------------------------------------

class ConfidenceScore(BaseModel):
    """Evidence-based confidence rating for a player on a title."""
    user_id: str
    title: str
    overall: float = Field(..., ge=0.0, le=1.0, description="Overall confidence 0-1")
    win_rate_30d: float = Field(0.0, ge=0.0, le=1.0)
    clutch_rate: float = Field(0.0, ge=0.0, le=1.0)
    consistency: float = Field(0.0, ge=0.0, le=1.0)
    recent_form: float = Field(0.0, ge=0.0, le=1.0)
    sample_size: int = Field(0, ge=0)
    computed_at: datetime | None = None


class ClutchPerformance(BaseModel):
    """Clutch and pressure conversion statistics."""
    user_id: str
    clutch_rate: float = Field(0.0, ge=0.0, le=1.0, description="Win rate in high-pressure moments")
    clutch_games: int = Field(0, ge=0)
    total_pressure_moments: int = Field(0, ge=0)
    pressure_conversion: float = Field(0.0, ge=0.0, le=1.0)
    comeback_rate: float = Field(0.0, ge=0.0, le=1.0)
    close_game_win_rate: float = Field(0.0, ge=0.0, le=1.0)


class MomentumState(BaseModel):
    """Current win/loss streak and recent form."""
    user_id: str
    session_id: str | None = None
    direction: MomentumDirection = MomentumDirection.STABLE
    streak_length: int = Field(0, ge=0)
    streak_type: str = Field("none", description="'win', 'loss', or 'none'")
    recent_results: list[bool] = Field(default_factory=list, description="Last N game outcomes")
    form_score: float = Field(0.5, ge=0.0, le=1.0, description="Weighted recent form")


class PreGameReadiness(BaseModel):
    """Composite pre-game readiness assessment."""
    user_id: str
    title: str
    level: ReadinessLevel = ReadinessLevel.MODERATE
    composite_score: float = Field(0.5, ge=0.0, le=1.0)
    confidence_factor: float = Field(0.5, ge=0.0, le=1.0)
    fatigue_factor: float = Field(0.5, ge=0.0, le=1.0)
    practice_factor: float = Field(0.5, ge=0.0, le=1.0)
    recent_form_factor: float = Field(0.5, ge=0.0, le=1.0)
    recommendation: str = Field("", description="Brief readiness recommendation")


# ---------------------------------------------------------------------------
# BenchmarkAI
# ---------------------------------------------------------------------------

class PercentileComparison(BaseModel):
    """Player stats compared to a target percentile."""
    user_id: str
    title: str
    target_percentile: int = Field(95, ge=1, le=100)
    player_percentile: int = Field(50, ge=1, le=100)
    dimensions: dict[str, float] = Field(default_factory=dict)
    gaps: dict[str, float] = Field(default_factory=dict, description="Gap to target per dimension")
    summary: str = ""


class DimensionScores(BaseModel):
    """All measurable performance dimensions for a player."""
    user_id: str
    title: str
    read_speed: float = Field(0.5, ge=0.0, le=1.0)
    user_defense: float = Field(0.5, ge=0.0, le=1.0)
    clutch: float = Field(0.5, ge=0.0, le=1.0)
    anti_meta: float = Field(0.5, ge=0.0, le=1.0)
    execution: float = Field(0.5, ge=0.0, le=1.0)
    mental: float = Field(0.5, ge=0.0, le=1.0)
    computed_at: datetime | None = None


class StandoutSkill(BaseModel):
    """A skill where the player is above average."""
    dimension: str
    score: float = Field(..., ge=0.0, le=1.0)
    percentile: int = Field(..., ge=1, le=100)
    description: str = ""


class StandoutSkillsReport(BaseModel):
    """Collection of standout skills for a player."""
    user_id: str
    title: str
    standout_skills: list[StandoutSkill] = Field(default_factory=list)
    top_skill: str = ""


class ImprovementVelocity(BaseModel):
    """Rate of improvement over time windows."""
    user_id: str
    title: str
    velocity_7d: float = Field(0.0, description="Improvement rate over 7 days")
    velocity_30d: float = Field(0.0, description="Improvement rate over 30 days")
    velocity_90d: float = Field(0.0, description="Improvement rate over 90 days")
    fastest_improving: str = Field("", description="Dimension improving fastest")
    declining: list[str] = Field(default_factory=list, description="Dimensions trending down")


# ---------------------------------------------------------------------------
# Narrative Engine
# ---------------------------------------------------------------------------

class WeeklyNarrative(BaseModel):
    """Coherent growth story from raw data over the past week."""
    user_id: str
    title: str
    narrative: str = Field("", description="Human-readable growth narrative")
    highlights: list[str] = Field(default_factory=list)
    lowlights: list[str] = Field(default_factory=list)
    key_stats: dict[str, Any] = Field(default_factory=dict)
    period_start: datetime | None = None
    period_end: datetime | None = None


class Milestone(BaseModel):
    """A detected player milestone."""
    user_id: str
    category: MilestoneCategory
    title: str = Field("", description="Short milestone title")
    description: str = Field("", description="Human-readable milestone description")
    achieved_at: datetime | None = None
    value: float | None = None


class GrowthTrajectory(BaseModel):
    """Trend lines for key metrics over a time window."""
    user_id: str
    title: str
    weeks: int = Field(4, ge=1)
    trends: dict[str, list[float]] = Field(default_factory=dict, description="Metric -> weekly values")
    overall_direction: MomentumDirection = MomentumDirection.STABLE
    projected_percentile: int | None = None


class SessionSummary(BaseModel):
    """Post-game narrative summary (not just stats)."""
    user_id: str
    session_id: str
    narrative: str = Field("", description="Post-game narrative")
    performance_rating: float = Field(0.5, ge=0.0, le=1.0)
    key_moments: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    areas_to_work_on: list[str] = Field(default_factory=list)
