"""Pydantic schemas for LoopAI — the self-improvement engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    """Classification of why a recommendation failed."""

    bad_read = "bad_read"
    bad_execution = "bad_execution"
    wrong_confidence = "wrong_confidence"
    wrong_opponent_model = "wrong_opponent_model"
    pressure_collapse = "pressure_collapse"
    stale_meta = "stale_meta"
    unknown = "unknown"


class InterventionType(str, Enum):
    """Types of corrective intervention LoopAI can suggest."""

    drill_assignment = "drill_assignment"
    confidence_recalibration = "confidence_recalibration"
    opponent_model_refresh = "opponent_model_refresh"
    meta_update = "meta_update"
    gameplan_revision = "gameplan_revision"
    mental_reset = "mental_reset"
    review_session = "review_session"


class DownstreamTarget(str, Enum):
    """Backbone systems that LoopAI can push updates to."""

    player_twin = "player_twin"
    impact_rank = "impact_rank"
    truth_engine = "truth_engine"
    gameplan_ai = "gameplan_ai"
    drill_bot = "drill_bot"
    anti_meta_lab = "anti_meta_lab"
    confidence_ai = "confidence_ai"


# ---------------------------------------------------------------------------
# Core result models
# ---------------------------------------------------------------------------


class RecommendationOutcome(BaseModel):
    """Evaluation of a single recommendation after a game."""

    recommendation_id: UUID
    session_id: UUID
    description: str = Field(..., description="What was recommended")
    was_followed: bool = Field(..., description="Did the player attempt it?")
    was_successful: bool | None = Field(
        None, description="Did following/ignoring it lead to a good outcome?"
    )
    confidence_at_time: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence when rec was made"
    )
    context_snapshot: dict = Field(
        default_factory=dict,
        description="Game state / opponent data at time of recommendation",
    )
    notes: str = ""


class FailureAttribution(BaseModel):
    """Detailed breakdown of why a recommendation failed."""

    id: UUID = Field(default_factory=uuid4)
    recommendation_id: UUID
    failure_type: FailureType
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="How confident the attribution is"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Supporting evidence for this classification"
    )
    suggested_intervention: InterventionType | None = None
    intervention_detail: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DownstreamUpdate(BaseModel):
    """Record of an update pushed to a downstream backbone system."""

    id: UUID = Field(default_factory=uuid4)
    target: DownstreamTarget
    payload_summary: str
    status: str = "pending"  # pending | sent | acknowledged | failed
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Pattern(BaseModel):
    """A recurring pattern detected across multiple sessions."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str = Field(..., description="Game title (e.g. madden26)")
    pattern_type: str = Field(
        ..., description="Category: failure_cluster, improvement_trend, regression, habit"
    )
    description: str
    frequency: int = Field(..., ge=1, description="How many sessions exhibit this")
    first_seen: datetime
    last_seen: datetime
    related_failure_types: list[FailureType] = Field(default_factory=list)
    severity: float = Field(
        ..., ge=0.0, le=1.0, description="How impactful this pattern is"
    )
    actionable: bool = True
    suggested_intervention: InterventionType | None = None


class LoopResult(BaseModel):
    """Complete output of a single post-game LoopAI processing cycle."""

    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    session_id: UUID
    title: str = Field(..., description="Game title")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    outcomes: list[RecommendationOutcome] = Field(default_factory=list)
    attributions: list[FailureAttribution] = Field(default_factory=list)
    downstream_updates: list[DownstreamUpdate] = Field(default_factory=list)
    patterns_detected: list[Pattern] = Field(default_factory=list)
    overall_accuracy: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of recommendations that were successful",
    )
    net_improvement_score: float = Field(
        ...,
        description="Delta vs. rolling average — positive means getting smarter",
    )
    summary: str = Field(
        ..., description="Human-readable summary of what was learned"
    )


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------


class SessionProcessRequest(BaseModel):
    """Payload for POST /loop/process-session."""

    user_id: UUID
    session_id: UUID
    title: str
    session_data: dict = Field(
        ..., description="Raw session data including game events, actions, outcomes"
    )
    recommendations_used: list[dict] = Field(
        default_factory=list,
        description="Recommendations that were active during this session",
    )


class AttributionDistribution(BaseModel):
    """Aggregated failure-type distribution for a player."""

    user_id: UUID
    title: str
    total_failures: int
    distribution: dict[FailureType, int]
    most_common: FailureType
    trend: str = Field(
        ..., description="improving | stable | declining"
    )


class LearningHistoryResponse(BaseModel):
    """Paginated learning history."""

    user_id: UUID
    title: str
    results: list[LoopResult]
    total: int


class PatternDetectionResponse(BaseModel):
    """Patterns detected for a player."""

    user_id: UUID
    title: str
    patterns: list[Pattern]
    total: int
