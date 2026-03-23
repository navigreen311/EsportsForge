"""Pydantic schemas for SchemeAI — concept stacking, coverage answers, hot routes."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CoverageType(str, enum.Enum):
    """Common Madden 26 coverage shells."""

    COVER_0 = "cover_0"
    COVER_1 = "cover_1"
    COVER_2 = "cover_2"
    COVER_2_MAN = "cover_2_man"
    COVER_3 = "cover_3"
    COVER_3_MATCH = "cover_3_match"
    COVER_4 = "cover_4"
    COVER_4_PALMS = "cover_4_palms"
    COVER_6 = "cover_6"
    MAN_PRESS = "man_press"
    MAN_OFF = "man_off"


class Situation(str, enum.Enum):
    """Game-state situations for contextual play-calling."""

    RED_ZONE = "red_zone"
    THIRD_AND_LONG = "3rd_and_long"
    THIRD_AND_SHORT = "3rd_and_short"
    GOAL_LINE = "goal_line"
    TWO_MINUTE = "2_minute"
    FOUR_MINUTE = "4_minute"
    OPENING_SCRIPT = "opening_script"
    BACKED_UP = "backed_up"
    FOURTH_DOWN = "4th_down"


class RouteType(str, enum.Enum):
    """Route modifications available as hot routes."""

    STREAK = "streak"
    SLANT = "slant"
    DRAG = "drag"
    CURL = "curl"
    COMEBACK = "comeback"
    OUT = "out"
    IN = "in"
    CORNER = "corner"
    POST = "post"
    FLAT = "flat"
    WHEEL = "wheel"
    FADE = "fade"
    TEXAS = "texas"
    ANGLE = "angle"
    MOTION = "motion"


class SchemeName(str, enum.Enum):
    """Recognized offensive scheme archetypes in Madden 26."""

    WEST_COAST = "west_coast"
    SPREAD = "spread"
    AIR_RAID = "air_raid"
    RUN_POWER = "run_power"
    RPO_HEAVY = "rpo_heavy"
    VERTICAL = "vertical"
    GUN_BUNCH = "gun_bunch"
    TRIPS = "trips"
    UNDER_CENTER = "under_center"
    PISTOL = "pistol"
    SINGLEBACK = "singleback"
    SHOTGUN = "shotgun"


# ---------------------------------------------------------------------------
# Core schemas
# ---------------------------------------------------------------------------

class Concept(BaseModel):
    """A single offensive concept that can be stacked with others."""

    name: str = Field(..., description="Concept name, e.g. 'Mesh', 'Flood', 'Smash'")
    formation: str = Field(..., description="Formation this concept runs from")
    play_name: str = Field(..., description="Actual play name in the playbook")
    primary_read: str = Field(..., description="First read on the concept")
    tags: list[str] = Field(default_factory=list, description="Tags: quick, deep, run, etc.")
    beats_coverages: list[CoverageType] = Field(
        default_factory=list, description="Coverages this concept is effective against"
    )
    down_distance_fit: list[str] = Field(
        default_factory=list, description="Down-distance situations where this fits"
    )
    stackable_with: list[str] = Field(
        default_factory=list, description="Other concept names this pairs well with"
    )


class CoverageAnswer(BaseModel):
    """A single answer to a specific coverage look."""

    coverage: CoverageType
    best_plays: list[str] = Field(..., description="Play names that beat this coverage")
    primary_read: str = Field(..., description="Where to look first")
    key_adjustment: Optional[str] = Field(
        None, description="Hot route or motion adjustment needed"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence in this answer"
    )


class CoverageMatrix(BaseModel):
    """Complete coverage answer matrix for a scheme."""

    scheme: str = Field(..., description="Scheme name")
    answers: list[CoverageAnswer] = Field(
        ..., description="One answer per coverage type"
    )
    generated_at: str = Field(..., description="ISO timestamp of generation")
    notes: Optional[str] = Field(None, description="AI commentary on scheme gaps")


class CoverageMatrixRequest(BaseModel):
    """Request body for building a coverage answer matrix."""

    scheme: SchemeName = Field(..., description="Scheme to analyze")
    formation_filter: Optional[str] = Field(
        None, description="Limit to a specific formation"
    )
    include_adjustments: bool = Field(
        True, description="Include hot route adjustments in answers"
    )


class HotRoute(BaseModel):
    """A suggested hot-route adjustment."""

    receiver: str = Field(..., description="Receiver position, e.g. 'WR1', 'TE', 'RB'")
    original_route: str = Field(..., description="Default route on the play")
    suggested_route: RouteType = Field(..., description="Recommended hot route")
    reason: str = Field(..., description="Why this beats the read coverage")
    expected_yards: Optional[float] = Field(
        None, description="Expected yards after catch"
    )


class HotRouteRequest(BaseModel):
    """Request body for hot route suggestions."""

    play_name: str = Field(..., description="Play to modify")
    coverage_read: CoverageType = Field(..., description="Pre-snap coverage read")
    formation: Optional[str] = Field(None, description="Current formation")


class SituationPlay(BaseModel):
    """A play recommended for a specific game situation."""

    play_name: str
    formation: str
    situation: Situation
    reason: str = Field(..., description="Why this play fits the situation")
    success_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Historical success rate in this spot"
    )
    tags: list[str] = Field(default_factory=list)


class SchemeTendency(BaseModel):
    """Analysis of play-calling tendencies and predictability."""

    total_plays_analyzed: int
    most_called_plays: list[dict[str, Any]] = Field(
        ..., description="Top 5 plays with call count"
    )
    formation_distribution: dict[str, float] = Field(
        ..., description="Formation usage percentages"
    )
    run_pass_ratio: dict[str, float] = Field(
        ..., description="{'run': 0.4, 'pass': 0.6}"
    )
    predictability_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="0.0 = perfectly balanced, 1.0 = completely predictable",
    )
    predictable_situations: list[str] = Field(
        default_factory=list,
        description="Situations where you are most predictable",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="AI suggestions to reduce predictability",
    )


class SchemeAnalysis(BaseModel):
    """Full breakdown of an offensive scheme."""

    scheme: str
    description: str = Field(..., description="Human-readable scheme overview")
    strengths: list[str]
    weaknesses: list[str]
    core_concepts: list[Concept]
    best_formations: list[str]
    coverage_answers: CoverageMatrix
    situation_plays: dict[str, list[SituationPlay]] = Field(
        default_factory=dict, description="Keyed by Situation value"
    )
    recommended_playbooks: list[str] = Field(
        default_factory=list, description="Madden 26 team playbooks that fit"
    )
