"""CFB RosterIQ schemas — depth chart analysis and dynasty roster projection."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class PlayerYear(str, Enum):
    """Player eligibility year."""

    FRESHMAN = "freshman"
    REDSHIRT_FRESHMAN = "redshirt_freshman"
    SOPHOMORE = "sophomore"
    REDSHIRT_SOPHOMORE = "redshirt_sophomore"
    JUNIOR = "junior"
    REDSHIRT_JUNIOR = "redshirt_junior"
    SENIOR = "senior"
    REDSHIRT_SENIOR = "redshirt_senior"


class DevelopmentTrait(str, Enum):
    """Player development trait."""

    NORMAL = "normal"
    IMPACT = "impact"
    STAR = "star"
    ELITE = "elite"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class DepthChartEntry(BaseModel):
    """A single position on the depth chart."""

    position: str
    depth: int = Field(..., ge=1, description="1=starter, 2=backup, etc.")
    player_name: str
    overall: int = Field(..., ge=40, le=99)
    year: PlayerYear
    development: DevelopmentTrait = Field(default=DevelopmentTrait.NORMAL)
    key_attributes: dict = Field(default_factory=dict)
    projected_overall_next_year: int = Field(default=0, ge=0, le=99)


class PositionGroup(BaseModel):
    """Analysis of a position group on the depth chart."""

    position: str
    starters: list[DepthChartEntry] = Field(default_factory=list)
    backups: list[DepthChartEntry] = Field(default_factory=list)
    avg_overall: float = Field(default=0.0, ge=0.0, le=99.0)
    depth_rating: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How deep this position group is (0=thin, 1=loaded).",
    )
    injury_vulnerability: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How much an injury would hurt (0=fine, 1=devastating).",
    )
    departures_next_year: int = Field(default=0, ge=0)


class DepthChartAnalysis(BaseModel):
    """Full school-specific depth chart analysis."""

    id: UUID = Field(default_factory=uuid4)
    school: str
    season_year: int = Field(default=2026)
    position_groups: list[PositionGroup] = Field(default_factory=list)
    team_overall: float = Field(default=0.0, ge=0.0, le=99.0)
    offense_rating: float = Field(default=0.0, ge=0.0, le=99.0)
    defense_rating: float = Field(default=0.0, ge=0.0, le=99.0)
    strongest_positions: list[str] = Field(default_factory=list)
    weakest_positions: list[str] = Field(default_factory=list)
    roster_balance_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How balanced the roster is across positions.",
    )
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectedPlayer(BaseModel):
    """A player's projected future state."""

    player_name: str
    position: str
    current_overall: int = Field(..., ge=40, le=99)
    projected_overall: int = Field(..., ge=40, le=99)
    year: PlayerYear
    development: DevelopmentTrait = Field(default=DevelopmentTrait.NORMAL)
    is_incoming_recruit: bool = Field(default=False)
    transfer_portal_risk: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Risk of entering the transfer portal.",
    )


class DynastyProjection(BaseModel):
    """Multi-year dynasty roster projection."""

    id: UUID = Field(default_factory=uuid4)
    school: str
    current_year: int = Field(default=2026)
    projection_years: int = Field(default=3, ge=1, le=10)
    yearly_snapshots: list[DepthChartAnalysis] = Field(default_factory=list)
    key_players_to_develop: list[ProjectedPlayer] = Field(default_factory=list)
    critical_departures: list[ProjectedPlayer] = Field(default_factory=list)
    projected_team_trajectory: list[float] = Field(
        default_factory=list,
        description="Projected team overall per year.",
    )
    championship_window: str = Field(
        default="",
        description="When the roster is projected to peak.",
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class DepthChartInput(BaseModel):
    """Input for depth chart analysis."""

    school: str
    roster: list[dict] = Field(
        default_factory=list,
        description="List of player dicts with position, overall, year, etc.",
    )
    scheme_type: str = Field(default="spread_rpo")


class DynastyProjectionInput(BaseModel):
    """Input for dynasty roster projection."""

    school: str
    roster: list[dict] = Field(default_factory=list)
    incoming_recruits: list[dict] = Field(default_factory=list)
    projection_years: int = Field(default=3, ge=1, le=10)


class RosterResponse(BaseModel):
    """Envelope for roster endpoints."""

    school: str
    depth_chart: DepthChartAnalysis | None = None
    projection: DynastyProjection | None = None
