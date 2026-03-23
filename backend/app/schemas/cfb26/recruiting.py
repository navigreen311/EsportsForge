"""RecruitingIQ schemas — dynasty recruiting optimizer, roster roadmap."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Position(str, Enum):
    """Football positions."""

    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    OL = "OL"
    DL = "DL"
    LB = "LB"
    CB = "CB"
    S = "S"
    K = "K"
    P = "P"
    ATH = "ATH"


class RecruitPriority(str, Enum):
    """Recruiting priority level."""

    MUST_HAVE = "must_have"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DEPTH = "depth"


class PipelineStage(str, Enum):
    """Where a recruit is in the pipeline."""

    IDENTIFIED = "identified"
    SCOUTED = "scouted"
    CONTACTED = "contacted"
    VISITED = "visited"
    OFFERED = "offered"
    COMMITTED = "committed"
    SIGNED = "signed"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class RecruitData(BaseModel):
    """Raw recruit data input."""

    name: str
    position: Position
    star_rating: int = Field(..., ge=1, le=5)
    overall_rating: int = Field(..., ge=40, le=99)
    state: str = Field(default="")
    high_school: str = Field(default="")
    top_schools: list[str] = Field(default_factory=list)
    interest_level: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Interest in your program (0-1).",
    )
    attributes: dict = Field(
        default_factory=dict,
        description="Speed, strength, agility, etc.",
    )
    pipeline_stage: PipelineStage = Field(default=PipelineStage.IDENTIFIED)


class RecruitEvaluation(BaseModel):
    """Evaluation of whether a recruit is worth pursuing."""

    recruit_name: str
    position: Position
    overall_grade: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall evaluation grade.",
    )
    scheme_fit: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well recruit fits your scheme.",
    )
    development_ceiling: float = Field(
        ..., ge=0.0, le=1.0,
        description="Projected ceiling after development.",
    )
    position_need_match: float = Field(
        ..., ge=0.0, le=1.0,
        description="How much this position is needed.",
    )
    commitment_likelihood: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probability of getting the commitment.",
    )
    worth_pursuing: bool = Field(
        ..., description="Final verdict on whether to pursue.",
    )
    reasoning: str = Field(default="")
    comparison_players: list[str] = Field(
        default_factory=list,
        description="Similar players for reference.",
    )


class RecruitingBoardEntry(BaseModel):
    """A single entry on the recruiting board."""

    recruit: RecruitData
    evaluation: RecruitEvaluation
    priority: RecruitPriority
    rank_on_board: int = Field(..., ge=1)
    action_items: list[str] = Field(default_factory=list)


class RecruitingBoard(BaseModel):
    """Optimized recruiting board with prioritized targets."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    school: str = Field(default="")
    season_year: int = Field(default=2026)
    entries: list[RecruitingBoardEntry] = Field(default_factory=list)
    total_scholarships_available: int = Field(default=25, ge=0)
    scholarships_committed: int = Field(default=0, ge=0)
    position_priorities: dict[str, RecruitPriority] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PositionNeed(BaseModel):
    """A specific position need in the roster."""

    position: Position
    urgency: RecruitPriority
    current_depth: int = Field(default=0, ge=0)
    ideal_depth: int = Field(default=2, ge=1)
    avg_overall_at_position: float = Field(default=0.0, ge=0.0, le=99.0)
    graduating_count: int = Field(
        default=0, ge=0,
        description="Players at this position leaving after this season.",
    )
    reasoning: str = Field(default="")


class YearPlan(BaseModel):
    """Roster plan for a single year."""

    year: int
    target_positions: list[PositionNeed] = Field(default_factory=list)
    scholarship_budget: int = Field(default=25, ge=0)
    key_departures: list[str] = Field(default_factory=list)
    key_targets: list[str] = Field(default_factory=list)
    projected_team_overall: float = Field(default=0.0, ge=0.0, le=99.0)


class RosterRoadmap(BaseModel):
    """Multi-year roster build plan."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    school: str = Field(default="")
    starting_overall: float = Field(default=0.0, ge=0.0, le=99.0)
    target_overall: float = Field(default=0.0, ge=0.0, le=99.0)
    year_plans: list[YearPlan] = Field(default_factory=list)
    total_years: int = Field(default=3, ge=1, le=10)
    philosophy: str = Field(
        default="",
        description="Recruiting philosophy summary.",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class DynastyStateInput(BaseModel):
    """Input representing current dynasty state."""

    user_id: str
    school: str
    season_year: int = Field(default=2026)
    current_roster: list[dict] = Field(
        default_factory=list,
        description="Current roster data.",
    )
    available_recruits: list[dict] = Field(
        default_factory=list,
        description="Available recruit pool.",
    )
    scholarships_available: int = Field(default=25, ge=0)
    scheme_type: str = Field(default="spread_rpo")
    conference: str = Field(default="")
    prestige: int = Field(default=50, ge=0, le=100)


class RosterInput(BaseModel):
    """Input representing current roster for needs analysis."""

    players: list[dict] = Field(
        default_factory=list,
        description="List of player dicts with position, overall, year, etc.",
    )
    scheme_type: str = Field(default="spread_rpo")


class RecruitingResponse(BaseModel):
    """Envelope for recruiting endpoints."""

    user_id: str
    board: RecruitingBoard | None = None
    roadmap: RosterRoadmap | None = None
    position_needs: list[PositionNeed] | None = None
