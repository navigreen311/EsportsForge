"""Schemas for Kill Sheet Generator — 5 plays proven to beat a specific opponent."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Situation(str, Enum):
    """Game situation category for situational kills."""
    RED_ZONE = "red_zone"
    THIRD_DOWN = "third_down"
    BLITZ = "blitz"
    GOAL_LINE = "goal_line"
    TWO_POINT = "two_point"


class FormationType(str, Enum):
    """Offensive formation type."""
    SHOTGUN = "shotgun"
    UNDER_CENTER = "under_center"
    PISTOL = "pistol"
    SINGLEBACK = "singleback"
    I_FORM = "i_form"
    GUN_BUNCH = "gun_bunch"
    EMPTY = "empty"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class OpponentTendency(BaseModel):
    """Observed tendency of an opponent."""
    category: str = Field(..., description="e.g. 'blitz_rate', 'cover_3_pct'")
    value: float
    sample_size: int = Field(0, ge=0)
    notes: str = ""


class OpponentData(BaseModel):
    """Scouting report on a specific opponent."""
    opponent_id: str
    opponent_name: str
    tendencies: list[OpponentTendency] = Field(default_factory=list)
    recent_games_analyzed: int = Field(0, ge=0)
    defensive_scheme: str = ""
    blitz_rate: float = Field(0.0, ge=0.0, le=1.0)
    man_coverage_rate: float = Field(0.0, ge=0.0, le=1.0)
    zone_coverage_rate: float = Field(0.0, ge=0.0, le=1.0)


class Roster(BaseModel):
    """User roster summary relevant to play selection."""
    qb_overall: int = Field(80, ge=0, le=99)
    rb_overall: int = Field(80, ge=0, le=99)
    wr1_overall: int = Field(80, ge=0, le=99)
    wr2_overall: int = Field(80, ge=0, le=99)
    te_overall: int = Field(80, ge=0, le=99)
    oline_avg: int = Field(80, ge=0, le=99)
    scheme_fit: str = Field("balanced", description="offensive scheme identity")


class KillSheetRequest(BaseModel):
    """Request to generate a kill sheet."""
    user_id: str
    opponent_data: OpponentData
    roster: Roster


class GameResult(BaseModel):
    """Post-game result for updating the kill sheet."""
    game_id: str
    opponent_id: str
    plays_used: list[str]
    plays_successful: list[str]
    final_score_user: int
    final_score_opponent: int
    notes: str = ""


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class RankedPlay(BaseModel):
    """A play ranked by effectiveness vs. a specific opponent."""
    play_name: str
    playbook: str = Field(..., description="Playbook or formation family")
    formation: FormationType
    concept: str = Field(..., description="e.g. 'crossing route', 'power run'")
    effectiveness_score: float = Field(..., ge=0.0, le=1.0)
    yards_per_attempt: float = Field(0.0, ge=0.0)
    opponent_weakness_exploited: str
    hot_route_adjustments: list[str] = Field(default_factory=list)
    setup_notes: str = ""


class ScoredPlay(RankedPlay):
    """RankedPlay with ConfidenceAI score attached."""
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="ConfidenceAI rating")
    confidence_reasoning: str = ""


class KillSheet(BaseModel):
    """5 plays proven to beat this specific opponent."""
    id: str = Field(..., description="Unique kill sheet identifier")
    user_id: str
    opponent_id: str
    opponent_name: str
    kills: list[RankedPlay] = Field(..., min_length=1, max_length=10, description="Primary kill plays (target 5)")
    generated_at: str = Field(..., description="ISO-8601 timestamp")
    version: int = Field(1, ge=1)
    notes: str = ""


class ScoredKillSheet(BaseModel):
    """Kill sheet with ConfidenceAI scores on every play."""
    id: str
    user_id: str
    opponent_id: str
    opponent_name: str
    kills: list[ScoredPlay]
    average_confidence: float = Field(..., ge=0.0, le=1.0)
    generated_at: str
    version: int = Field(1, ge=1)


class SituationalKill(BaseModel):
    """A kill play tied to a specific situation."""
    situation: Situation
    play: RankedPlay
    situation_success_rate: float = Field(..., ge=0.0, le=1.0)


class SituationalKills(BaseModel):
    """Situational kill collections — red zone, 3rd down, blitz beaters."""
    opponent_id: str
    red_zone_kills: list[SituationalKill] = Field(default_factory=list)
    third_down_kills: list[SituationalKill] = Field(default_factory=list)
    blitz_kills: list[SituationalKill] = Field(default_factory=list)
    goal_line_kills: list[SituationalKill] = Field(default_factory=list)
    two_point_kills: list[SituationalKill] = Field(default_factory=list)
