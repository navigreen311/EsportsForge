"""Pydantic schemas for DrillBot, AdaptAI, ConfidenceAI, and ProofAI services."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DrillType(str, Enum):
    """Classification of drill focus area."""

    MECHANICAL = "mechanical"
    DECISION = "decision"
    KNOWLEDGE = "knowledge"
    TACTICAL = "tactical"
    REACTION = "reaction"
    COMPOSURE = "composure"


class DrillStatus(str, Enum):
    """Current state of a drill."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    """Risk classification for a recommendation."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceType(str, Enum):
    """Type of evidence supporting a recommendation."""

    STATISTICAL = "statistical"
    HISTORICAL = "historical"
    PATTERN = "pattern"
    COMPARABLE_CASE = "comparable_case"
    EXPERT_HEURISTIC = "expert_heuristic"


# ---------------------------------------------------------------------------
# DrillBot schemas
# ---------------------------------------------------------------------------

class DrillSpec(BaseModel):
    """Specification for a single drill targeting a weakness."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Game title (e.g. 'madden26').")
    weakness_label: str = Field(..., description="The weakness this drill targets.")
    drill_type: DrillType = Field(..., description="Category of the drill.")
    name: str = Field(..., description="Human-readable drill name.")
    description: str = Field(default="", description="What the player should practice.")
    instructions: list[str] = Field(default_factory=list, description="Step-by-step instructions.")
    reps_required: int = Field(default=10, ge=1, description="Number of reps to complete.")
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="Difficulty level 0-1.")
    estimated_minutes: int = Field(default=5, ge=1, description="Estimated time to complete.")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DrillSession(BaseModel):
    """A player's session working through a drill."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    drill_id: UUID
    drill_spec: DrillSpec
    status: DrillStatus = Field(default=DrillStatus.PENDING)
    reps_completed: int = Field(default=0, ge=0)
    reps_successful: int = Field(default=0, ge=0)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    current_difficulty: float = Field(default=0.5, ge=0.0, le=1.0)

    @property
    def success_rate(self) -> float:
        """Rolling success rate for this session."""
        if self.reps_completed == 0:
            return 0.0
        return self.reps_successful / self.reps_completed

    @property
    def is_complete(self) -> bool:
        """Whether the required reps have been completed."""
        return self.reps_completed >= self.drill_spec.reps_required


class DrillResult(BaseModel):
    """Outcome of a completed drill session."""

    drill_id: UUID
    user_id: str
    weakness_label: str
    reps_completed: int
    reps_successful: int
    success_rate: float = Field(..., ge=0.0, le=1.0)
    difficulty_at_end: float = Field(..., ge=0.0, le=1.0)
    improvement_signal: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Positive = improving, negative = regressing.",
    )
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class DrillQueue(BaseModel):
    """Priority-ordered list of drills for a player."""

    user_id: str
    title: str
    drills: list[DrillSession] = Field(default_factory=list)
    total_estimated_minutes: int = Field(default=0, ge=0)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def pending_count(self) -> int:
        return sum(1 for d in self.drills if d.status == DrillStatus.PENDING)


class PersonalizedDrill(BaseModel):
    """A drill customized to a player's specific weakness and skill level."""

    user_id: str
    drill_spec: DrillSpec
    reason: str = Field(..., description="Why this drill was chosen.")
    priority: int = Field(default=1, ge=1, description="1 = highest priority.")
    expected_improvement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Projected improvement in weakness area.",
    )


# ---------------------------------------------------------------------------
# AdaptAI schemas
# ---------------------------------------------------------------------------

class SeriesAnalysis(BaseModel):
    """Analysis of what worked and what didn't in a series."""

    series_id: str = Field(default="", description="Identifier for the series.")
    games_played: int = Field(default=0, ge=0)
    wins: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    strengths_exploited: list[str] = Field(default_factory=list)
    weaknesses_exposed: list[str] = Field(default_factory=list)
    opponent_patterns: list[str] = Field(default_factory=list)
    momentum_shifts: list[str] = Field(default_factory=list)
    key_moments: list[str] = Field(default_factory=list)


class AdaptRecommendation(BaseModel):
    """ONE decisive between-series adjustment recommendation."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    adjustment: str = Field(..., description="The ONE thing to change.")
    reasoning: str = Field(..., description="Why this is the highest-impact change.")
    implementation: str = Field(
        ..., description="Exactly how to execute this adjustment."
    )
    expected_impact: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Projected impact on win probability.",
    )
    time_to_implement: str = Field(
        default="immediate",
        description="How long this takes to implement (e.g. 'immediate', '5 minutes').",
    )
    analysis: SeriesAnalysis | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ConfidenceAI schemas
# ---------------------------------------------------------------------------

class ConfidenceFactor(BaseModel):
    """A single factor driving confidence up or down."""

    factor: str = Field(..., description="Name of the factor.")
    direction: str = Field(..., description="'positive' or 'negative'.")
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="How much this factor matters."
    )
    explanation: str = Field(default="", description="Why this factor matters.")


class ConfidenceScore(BaseModel):
    """Confidence assessment for a recommendation."""

    recommendation_id: UUID = Field(default_factory=uuid4)
    confidence_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence percentage (0-100).",
    )
    risk_level: RiskLevel
    factors: list[ConfidenceFactor] = Field(default_factory=list)
    calibrated: bool = Field(
        default=False,
        description="Whether this score has been calibrated via Truth Engine.",
    )
    explanation: str = Field(
        default="", description="Human-readable confidence summary."
    )
    scored_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def confidence_normalized(self) -> float:
        """Confidence as 0-1 float."""
        return self.confidence_pct / 100.0


# ---------------------------------------------------------------------------
# ProofAI schemas
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """A single piece of evidence supporting a recommendation."""

    id: UUID = Field(default_factory=uuid4)
    evidence_type: EvidenceType
    title: str = Field(..., description="Short evidence label.")
    detail: str = Field(default="", description="Full evidence description.")
    data_points: list[str] = Field(
        default_factory=list, description="Specific data backing this evidence."
    )
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How strong this evidence is (0-1).",
    )


class ComparableCase(BaseModel):
    """A historical situation similar to the current one."""

    id: UUID = Field(default_factory=uuid4)
    situation_summary: str = Field(..., description="What was the situation.")
    action_taken: str = Field(..., description="What the player/team did.")
    outcome: str = Field(..., description="What happened.")
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How similar this case is to current situation (0-1).",
    )
    source: str = Field(default="historical_data", description="Where this case came from.")


class ProofPackage(BaseModel):
    """Complete evidence package for a recommendation — war room briefing."""

    id: UUID = Field(default_factory=uuid4)
    recommendation_id: UUID
    recommendation_summary: str = Field(..., description="The recommendation being proven.")
    reason: str = Field(..., description="Core reason this recommendation makes sense.")
    evidence: list[Evidence] = Field(default_factory=list)
    comparable_cases: list[ComparableCase] = Field(default_factory=list)
    overall_evidence_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregate evidence strength.",
    )
    briefing_summary: str = Field(
        default="",
        description="War room briefing format summary.",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    @property
    def comparable_case_count(self) -> int:
        return len(self.comparable_cases)
