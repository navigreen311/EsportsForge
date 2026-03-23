"""SchemeDepthAI schemas — playbook analysis, mastery, option reads, counters."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SchemeType(str, Enum):
    """CFB offensive scheme archetypes."""

    TRIPLE_OPTION = "triple_option"
    AIR_RAID = "air_raid"
    SPREAD_RPO = "spread_rpo"
    FLEXBONE = "flexbone"
    WEST_COAST = "west_coast"
    PRO_STYLE = "pro_style"
    POWER_RUN = "power_run"
    PISTOL = "pistol"


class MasteryTier(str, Enum):
    """Mastery level tiers."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class PlayType(str, Enum):
    """Option/RPO play type classification."""

    TRIPLE_OPTION = "triple_option"
    SPEED_OPTION = "speed_option"
    ZONE_READ = "zone_read"
    RPO_BUBBLE = "rpo_bubble"
    RPO_SLANT = "rpo_slant"
    RPO_GLANCE = "rpo_glance"
    PLAY_ACTION = "play_action"
    SCREEN = "screen"
    QB_DRAW = "qb_draw"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class ConceptMastery(BaseModel):
    """Mastery of a single scheme concept."""

    concept_name: str = Field(..., description="Name of the scheme concept.")
    proficiency: float = Field(
        ..., ge=0.0, le=1.0,
        description="Proficiency score (0-1).",
    )
    reps_completed: int = Field(default=0, ge=0)
    last_practiced: datetime | None = None


class FormationAnalysis(BaseModel):
    """Analysis of a single formation within a playbook."""

    formation_name: str
    play_count: int = Field(default=0, ge=0)
    avg_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    best_situations: list[str] = Field(default_factory=list)
    weakness_situations: list[str] = Field(default_factory=list)


class PlaybookAnalysis(BaseModel):
    """Full playbook mastery analysis result."""

    id: UUID = Field(default_factory=uuid4)
    scheme_type: SchemeType
    total_plays: int = Field(default=0, ge=0)
    formations: list[FormationAnalysis] = Field(default_factory=list)
    overall_mastery: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall playbook mastery score.",
    )
    strongest_concepts: list[str] = Field(default_factory=list)
    weakest_concepts: list[str] = Field(default_factory=list)
    diversity_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How diverse the play calling is (0=predictable, 1=varied).",
    )
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class MasteryLevel(BaseModel):
    """User's mastery level for a specific scheme."""

    user_id: str
    scheme_type: SchemeType
    tier: MasteryTier
    score: float = Field(..., ge=0.0, le=1.0)
    concepts_mastered: list[ConceptMastery] = Field(default_factory=list)
    games_played_with_scheme: int = Field(default=0, ge=0)
    win_rate_with_scheme: float = Field(default=0.0, ge=0.0, le=1.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SchemeProgression(BaseModel):
    """Next concepts to learn for scheme progression."""

    user_id: str
    current_tier: MasteryTier
    next_tier: MasteryTier
    progress_to_next: float = Field(
        ..., ge=0.0, le=1.0,
        description="Progress toward next tier (0-1).",
    )
    next_concepts: list[str] = Field(
        ..., description="Ordered list of concepts to learn next.",
    )
    recommended_drills: list[str] = Field(default_factory=list)
    estimated_hours_to_next_tier: float = Field(default=0.0, ge=0.0)


class OptionRead(BaseModel):
    """A single read in an option/RPO progression."""

    read_number: int = Field(..., ge=1, description="1=first read, 2=second, etc.")
    defender_key: str = Field(
        ..., description="Which defender to read (e.g. 'DE', 'OLB', 'safety').",
    )
    give_trigger: str = Field(
        ..., description="What the defender does that triggers giving the ball.",
    )
    pull_trigger: str = Field(
        ..., description="What the defender does that triggers pulling/keeping.",
    )
    tip: str = Field(default="", description="Pro tip for this read.")


class OptionReadProgression(BaseModel):
    """Full read progression for an option/RPO play."""

    play_type: PlayType
    reads: list[OptionRead] = Field(default_factory=list)
    pre_snap_keys: list[str] = Field(
        default_factory=list,
        description="Pre-snap indicators to look for.",
    )
    tempo_recommendation: str = Field(
        default="", description="Recommended tempo for this play.",
    )


class CounterScheme(BaseModel):
    """Counter strategy against an opponent's scheme."""

    opponent_scheme: SchemeType
    counter_formations: list[str] = Field(default_factory=list)
    counter_plays: list[str] = Field(default_factory=list)
    key_adjustments: list[str] = Field(default_factory=list)
    defensive_keys: list[str] = Field(
        default_factory=list,
        description="What to look for defensively against this scheme.",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Confidence in this counter strategy.",
    )


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class PlaybookInput(BaseModel):
    """Input for playbook analysis."""

    scheme_type: SchemeType
    plays: list[dict] = Field(
        default_factory=list,
        description="List of play data dicts with name, formation, success_rate, etc.",
    )
    game_logs: list[dict] = Field(
        default_factory=list,
        description="Recent game log data for context.",
    )


class SchemeAnalysisResponse(BaseModel):
    """Envelope for scheme analysis endpoints."""

    user_id: str
    analysis: PlaybookAnalysis
    mastery: MasteryLevel
    progression: SchemeProgression
