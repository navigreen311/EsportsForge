"""ImpactRank schemas — scoring, ranking, and prioritization models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WeaknessCategory(str, Enum):
    """Classification of weakness type."""

    MECHANICAL = "mechanical"
    DECISION = "decision"
    KNOWLEDGE = "knowledge"
    MENTAL = "mental"
    TACTICAL = "tactical"


class OutcomeVerdict(str, Enum):
    """Outcome after a player attempts a fix."""

    IMPROVED = "improved"
    NO_CHANGE = "no_change"
    REGRESSED = "regressed"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class ImpactScore(BaseModel):
    """Quantifies win-rate damage of a single weakness."""

    win_rate_damage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated fraction of games lost due to this weakness (0-1).",
    )
    frequency: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How often this weakness manifests per game (0-1).",
    )
    severity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How bad it is when it manifests (0-1).",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Statistical confidence in this estimate.",
    )

    @property
    def composite(self) -> float:
        """Composite impact = frequency * severity, weighted by confidence."""
        return self.frequency * self.severity * self.confidence


class FixScore(BaseModel):
    """Scores a proposed fix by ROI metrics."""

    expected_lift: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Projected win-rate improvement if fix is mastered (0-1).",
    )
    time_to_master_hours: float = Field(
        ...,
        gt=0.0,
        description="Estimated hours of focused practice to master this fix.",
    )
    execution_transfer_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability the player can actually execute this fix in-game (0-1).",
    )

    @property
    def roi(self) -> float:
        """ROI = (expected_lift * transfer_rate) / time_to_master."""
        if self.time_to_master_hours == 0:
            return 0.0
        return (self.expected_lift * self.execution_transfer_rate) / self.time_to_master_hours


# ---------------------------------------------------------------------------
# Domain entities
# ---------------------------------------------------------------------------

class Weakness(BaseModel):
    """A detected player weakness."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Game title (e.g. 'madden26').")
    category: WeaknessCategory
    label: str = Field(..., description="Human-readable weakness name.")
    description: str = Field(default="", description="Detailed explanation.")
    evidence: list[str] = Field(default_factory=list, description="Supporting data points.")
    impact_score: ImpactScore | None = None
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class Fix(BaseModel):
    """A proposed fix for a weakness."""

    id: UUID = Field(default_factory=uuid4)
    weakness_id: UUID
    label: str = Field(..., description="Short name of the fix.")
    description: str = Field(default="", description="What the player should do.")
    drill: str = Field(default="", description="Specific practice drill or routine.")
    fix_score: FixScore | None = None


class ImpactRanking(BaseModel):
    """A ranked weakness with its best fix attached."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    weakness: Weakness
    best_fix: Fix | None = None
    rank: int = Field(..., ge=1, description="1 = highest priority.")
    composite_score: float = Field(
        default=0.0,
        description="Combined score used for ordering (higher = more urgent).",
    )
    suppressed: bool = Field(
        default=False,
        description="True if below ROI threshold — hidden from player.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PriorityRecommendation(BaseModel):
    """The ONE thing the player should fix next."""

    user_id: str
    title: str
    ranking: ImpactRanking
    message: str = Field(
        ...,
        description="Direct, actionable message to the player.",
    )


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class OutcomeReport(BaseModel):
    """Payload when reporting an outcome for a ranking."""

    verdict: OutcomeVerdict
    notes: str = ""
    games_played: int = Field(default=1, ge=1)
    observed_lift: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Measured win-rate change since fix was applied.",
    )


class RecalculateRequest(BaseModel):
    """Optional body for recalculate endpoint."""

    title: str = Field(..., description="Game title to recalculate for.")


class ImpactRankResponse(BaseModel):
    """Envelope for a list of rankings."""

    user_id: str
    title: str
    rankings: list[ImpactRanking]
    suppressed_count: int = 0
