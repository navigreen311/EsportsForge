"""Schemas for RosterIQ — personnel analysis, patch-adjusted ratings, speed mismatches."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Position(str, Enum):
    QB = "QB"
    HB = "HB"
    FB = "FB"
    WR = "WR"
    TE = "TE"
    LT = "LT"
    LG = "LG"
    C = "C"
    RG = "RG"
    RT = "RT"
    LE = "LE"
    RE = "RE"
    DT = "DT"
    LOLB = "LOLB"
    MLB = "MLB"
    ROLB = "ROLB"
    CB = "CB"
    FS = "FS"
    SS = "SS"
    K = "K"
    P = "P"


class SchemeType(str, Enum):
    SPREAD = "spread"
    WEST_COAST = "west_coast"
    AIR_RAID = "air_raid"
    POWER_RUN = "power_run"
    RPO_HEAVY = "rpo_heavy"
    ZONE_RUN = "zone_run"
    BALANCED = "balanced"


class DefensiveScheme(str, Enum):
    COVER_3 = "cover_3"
    COVER_2 = "cover_2"
    MAN_PRESS = "man_press"
    TAMPA_2 = "tampa_2"
    MULTIPLE = "multiple"
    HYBRID_34 = "hybrid_34"
    FOUR_THREE = "four_three"


class MismatchSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Player / Roster primitives
# ---------------------------------------------------------------------------

class PlayerRating(BaseModel):
    """Core player ratings from Madden 26."""
    overall: int = Field(..., ge=0, le=99, description="Overall rating")
    speed: int = Field(..., ge=0, le=99)
    acceleration: int = Field(..., ge=0, le=99)
    agility: int = Field(..., ge=0, le=99)
    strength: int = Field(..., ge=0, le=99)
    awareness: int = Field(..., ge=0, le=99)
    catching: int | None = Field(None, ge=0, le=99)
    route_running: int | None = Field(None, ge=0, le=99)
    throw_power: int | None = Field(None, ge=0, le=99)
    throw_accuracy_short: int | None = Field(None, ge=0, le=99)
    throw_accuracy_mid: int | None = Field(None, ge=0, le=99)
    throw_accuracy_deep: int | None = Field(None, ge=0, le=99)
    block_shed: int | None = Field(None, ge=0, le=99)
    tackle: int | None = Field(None, ge=0, le=99)
    man_coverage: int | None = Field(None, ge=0, le=99)
    zone_coverage: int | None = Field(None, ge=0, le=99)
    press: int | None = Field(None, ge=0, le=99)


class Player(BaseModel):
    """A single rostered player."""
    name: str
    position: Position
    team: str
    ratings: PlayerRating
    archetype: str | None = None
    dev_trait: str | None = Field(None, description="Normal / Star / Superstar / X-Factor")


class RosterData(BaseModel):
    """Full roster payload sent by the client."""
    team_name: str
    players: list[Player]
    patch_version: str | None = Field(None, description="Current Madden patch, e.g. '1.06'")


# ---------------------------------------------------------------------------
# RosterIQ output models
# ---------------------------------------------------------------------------

class PositionGroupGrade(BaseModel):
    """Letter-grade + numeric score for a position group."""
    group: str = Field(..., description="e.g. 'WR Corps', 'Defensive Line'")
    grade: str = Field(..., description="A+ through F")
    score: float = Field(..., ge=0, le=100)
    strengths: list[str] = []
    weaknesses: list[str] = []


class RosterAnalysis(BaseModel):
    """Complete roster breakdown returned by RosterIQ.analyze_roster."""
    team_name: str
    overall_grade: str
    overall_score: float = Field(..., ge=0, le=100)
    position_grades: list[PositionGroupGrade]
    top_players: list[Player]
    biggest_needs: list[str]
    scheme_fit: SchemeType
    summary: str


class PersonnelPackage(BaseModel):
    """An available personnel grouping (e.g. 11 personnel = 1 RB, 1 TE)."""
    code: str = Field(..., description="Personnel code like '11', '12', '21', '22', '13'")
    description: str = Field(..., description="e.g. '1 RB, 1 TE, 3 WR'")
    available_players: dict[str, list[str]] = Field(
        ..., description="Position -> list of player names slotted in"
    )
    effectiveness_score: float = Field(..., ge=0, le=100)
    best_against: list[str] = Field(
        default_factory=list, description="Defensive looks this package exploits"
    )


class SpeedMismatch(BaseModel):
    """An exploitable speed gap between an offensive and defensive player."""
    offensive_player: str
    offensive_position: Position
    offensive_speed: int
    defensive_player: str
    defensive_position: Position
    defensive_speed: int
    speed_delta: int = Field(..., description="Positive means offense is faster")
    severity: MismatchSeverity
    exploit_tip: str = Field(..., description="How to attack this mismatch")


class SchemeRecommendation(BaseModel):
    """Best scheme fit for a given roster."""
    primary_scheme: SchemeType
    confidence: float = Field(..., ge=0, le=1.0)
    reasoning: str
    alternate_scheme: SchemeType | None = None
    key_players_for_scheme: list[str] = []
    playbook_suggestions: list[str] = []


class AdjustedRatings(BaseModel):
    """Player ratings after patch adjustments."""
    player_name: str
    patch_version: str
    original_overall: int
    adjusted_overall: int
    rating_changes: dict[str, int] = Field(
        ..., description="Attribute -> delta (positive = buff, negative = nerf)"
    )
    net_impact: str = Field(..., description="'buffed', 'nerfed', or 'unchanged'")


class RatingChange(BaseModel):
    """A single rating change from a patch."""
    player_name: str
    position: Position
    team: str
    attribute: str
    old_value: int
    new_value: int
    delta: int
    impact_summary: str


class HiddenGem(BaseModel):
    """An underrated player that fits the current scheme well."""
    player: Player
    gem_score: float = Field(..., ge=0, le=100, description="How underrated relative to scheme")
    reasoning: str
    best_role: str = Field(..., description="Ideal usage in the scheme")
    comparable_to: str | None = Field(None, description="Higher-rated player with similar profile")


# ---------------------------------------------------------------------------
# API request / response wrappers
# ---------------------------------------------------------------------------

class AnalyzeRosterRequest(BaseModel):
    roster: RosterData


class AnalyzeRosterResponse(BaseModel):
    analysis: RosterAnalysis
    personnel_packages: list[PersonnelPackage]
    hidden_gems: list[HiddenGem]


class SpeedMismatchRequest(BaseModel):
    offense_roster: RosterData
    defense_roster: RosterData


class SpeedMismatchResponse(BaseModel):
    mismatches: list[SpeedMismatch]
    top_exploit: SpeedMismatch | None = None


class PatchImpactRequest(BaseModel):
    patch_notes: str
    patch_version: str


class PatchImpactResponse(BaseModel):
    patch_version: str
    total_changes: int
    rating_changes: list[RatingChange]
    biggest_winners: list[str]
    biggest_losers: list[str]
