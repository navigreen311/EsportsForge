"""Schemas for MatchupAI and ReadAI — matchup advantages, coverage reads, blitz detection."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.madden26.roster import (
    Player,
    Position,
    RosterData,
    PersonnelPackage,
    MismatchSeverity,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CoverageType(str, Enum):
    COVER_0 = "cover_0"
    COVER_1 = "cover_1"
    COVER_2 = "cover_2"
    COVER_3 = "cover_3"
    COVER_4 = "cover_4"
    COVER_6 = "cover_6"
    MAN = "man"
    ZONE = "zone"
    MAN_BLITZ = "man_blitz"


class BlitzSource(str, Enum):
    MLB = "mlb"
    OLB = "olb"
    CB = "cb"
    SS = "ss"
    FS = "fs"
    DB_BLITZ = "db_blitz"
    SIMULATED = "simulated"
    NONE = "none"


class MotionType(str, Enum):
    JET = "jet"
    ORBIT = "orbit"
    SHIFT = "shift"
    TRADE = "trade"
    BUNCH = "bunch"
    STACK = "stack"


class AdvantageType(str, Enum):
    SPEED = "speed"
    SIZE = "size"
    ROUTE_RUNNING = "route_running"
    COVERAGE_BEATER = "coverage_beater"
    SCHEME = "scheme"
    PERSONNEL = "personnel"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ---------------------------------------------------------------------------
# MatchupAI models
# ---------------------------------------------------------------------------

class MatchupAdvantage(BaseModel):
    """A pre-snap personnel advantage identified by MatchupAI."""
    advantage_type: AdvantageType
    offensive_player: str
    offensive_position: Position
    defensive_player: str
    defensive_position: Position
    advantage_score: float = Field(..., ge=0, le=100)
    severity: MismatchSeverity
    description: str
    suggested_play_concepts: list[str] = []


class LeverageMatchup(BaseModel):
    """The best mismatch to isolate and exploit from a given formation."""
    target_player: str
    target_position: Position
    matched_against: str
    matched_position: Position
    leverage_score: float = Field(..., ge=0, le=100)
    route_suggestion: str
    formation_alignment: str = Field(..., description="Where the target lines up")
    reasoning: str


class MotionSuggestion(BaseModel):
    """Recommended pre-snap motion to create or confirm a favorable matchup."""
    motion_type: MotionType
    motion_player: str
    purpose: str = Field(..., description="What the motion accomplishes")
    reveals: str = Field(..., description="What coverage info this motion reveals")
    if_man: str = Field(..., description="What to do if motion confirms man coverage")
    if_zone: str = Field(..., description="What to do if motion confirms zone coverage")
    confidence: ConfidenceLevel


class GroupingEvaluation(BaseModel):
    """Evaluation of how a personnel grouping performs against a defensive look."""
    grouping_code: str
    defense_look: str
    effectiveness_score: float = Field(..., ge=0, le=100)
    strengths: list[str]
    vulnerabilities: list[str]
    recommended_plays: list[str]
    verdict: str


class MatchupResult(BaseModel):
    """Historical matchup result for tracking."""
    game_id: str
    opponent_id: str
    opponent_name: str
    user_score: int
    opponent_score: int
    result: str = Field(..., description="'win', 'loss', or 'draw'")
    offensive_yards: int | None = None
    defensive_yards_allowed: int | None = None
    key_matchup_exploited: str | None = None
    timestamp: str


# ---------------------------------------------------------------------------
# ReadAI models
# ---------------------------------------------------------------------------

class CoverageRead(BaseModel):
    """Pre-snap coverage identification."""
    primary_coverage: CoverageType
    confidence: ConfidenceLevel
    indicators: list[str] = Field(
        ..., description="Visual cues that suggest this coverage"
    )
    vulnerable_zones: list[str] = Field(
        default_factory=list, description="Areas of the field that are soft"
    )
    recommended_targets: list[str] = Field(
        default_factory=list, description="Routes/players to attack this coverage"
    )


class BlitzRead(BaseModel):
    """Pre-snap blitz detection."""
    blitz_detected: bool
    blitz_probability: float = Field(..., ge=0, le=1.0)
    likely_source: BlitzSource
    number_of_rushers: int = Field(..., ge=3, le=8)
    hot_route_suggestion: str | None = Field(
        None, description="Quick throw to beat the blitz"
    )
    protection_adjustment: str | None = Field(
        None, description="Blocking adjustment to pick up the blitz"
    )
    indicators: list[str] = []


class TendencyPattern(BaseModel):
    """A detected pattern in opponent behavior."""
    pattern_name: str
    description: str
    frequency: float = Field(..., ge=0, le=1.0, description="How often this occurs (0-1)")
    situation: str = Field(..., description="Game situation where pattern appears")
    counter_strategy: str
    sample_size: int = Field(..., ge=1, description="Number of plays analyzed")
    confidence: ConfidenceLevel


class Audible(BaseModel):
    """Recommended audible based on the defensive look."""
    original_play: str
    audible_to: str
    reason: str
    expected_gain: str = Field(..., description="Expected yardage or outcome")
    confidence: ConfidenceLevel
    risk_level: MismatchSeverity


# ---------------------------------------------------------------------------
# API request / response wrappers
# ---------------------------------------------------------------------------

class FindAdvantagesRequest(BaseModel):
    offense: RosterData
    defense: RosterData
    formation: str | None = None


class FindAdvantagesResponse(BaseModel):
    advantages: list[MatchupAdvantage]
    best_personnel: str | None = Field(None, description="Best personnel package code")
    leverage_matchup: LeverageMatchup | None = None
    motion_suggestion: MotionSuggestion | None = None


class ReadCoverageRequest(BaseModel):
    """Pre-snap read request."""
    pre_snap_info: dict = Field(
        ..., description="Defensive alignment details: safety depth, corner alignment, LB position"
    )
    current_play: str | None = None
    opponent_history: list[dict] | None = None


class ReadCoverageResponse(BaseModel):
    coverage_read: CoverageRead
    blitz_read: BlitzRead
    audible: Audible | None = None
    tendency_patterns: list[TendencyPattern] = []


class MatchupHistoryResponse(BaseModel):
    opponent_id: str
    total_games: int
    wins: int
    losses: int
    draws: int
    win_rate: float = Field(..., ge=0, le=1.0)
    results: list[MatchupResult]
    opponent_tendencies: list[TendencyPattern] = []
