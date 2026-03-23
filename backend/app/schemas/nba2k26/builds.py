"""NBA 2K26 build-related schemas — builds, badges, attribute thresholds, meta."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Position(str, Enum):
    """NBA 2K26 player positions."""

    PG = "pg"
    SG = "sg"
    SF = "sf"
    PF = "pf"
    C = "c"


class Archetype(str, Enum):
    """Build archetypes in NBA 2K26."""

    SHOT_CREATOR = "shot_creator"
    SLASHER = "slasher"
    STRETCH = "stretch"
    GLASS_CLEANER = "glass_cleaner"
    PLAYMAKER = "playmaker"
    LOCKDOWN = "lockdown"
    TWO_WAY = "two_way"
    INSIDE_BIG = "inside_big"
    SHARPSHOOTER = "sharpshooter"
    POST_SCORER = "post_scorer"


class BadgeTier(str, Enum):
    """Badge level tiers."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    HALL_OF_FAME = "hall_of_fame"
    LEGEND = "legend"


class BadgeCategory(str, Enum):
    """Badge categories."""

    FINISHING = "finishing"
    SHOOTING = "shooting"
    PLAYMAKING = "playmaking"
    DEFENSE = "defense"


class MetaTier(str, Enum):
    """Meta tier ranking for builds."""

    S_TIER = "s_tier"
    A_TIER = "a_tier"
    B_TIER = "b_tier"
    C_TIER = "c_tier"
    D_TIER = "d_tier"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class Badge(BaseModel):
    """A single badge with its tier and unlock requirements."""

    name: str = Field(..., description="Badge name (e.g. 'Agent', 'Limitless Range').")
    category: BadgeCategory
    tier: BadgeTier
    unlock_attribute: str = Field(
        ..., description="Attribute that unlocks this badge (e.g. 'three_point_shot').",
    )
    unlock_threshold: int = Field(
        ..., ge=0, le=99, description="Minimum attribute value to unlock this tier.",
    )
    description: str = Field(default="", description="What this badge does in-game.")


class AttributeThreshold(BaseModel):
    """An attribute threshold breakpoint — where new animations or abilities unlock."""

    attribute_name: str = Field(..., description="Attribute name (e.g. 'ball_handle').")
    current_value: int = Field(..., ge=25, le=99)
    next_threshold: int = Field(..., ge=25, le=99)
    unlocks_at_threshold: list[str] = Field(
        default_factory=list,
        description="Animations or abilities unlocked at next threshold.",
    )
    priority: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How important hitting this threshold is (0-1).",
    )


class BuildAttributes(BaseModel):
    """Core attribute block for an NBA 2K26 build."""

    close_shot: int = Field(default=25, ge=25, le=99)
    driving_layup: int = Field(default=25, ge=25, le=99)
    driving_dunk: int = Field(default=25, ge=25, le=99)
    standing_dunk: int = Field(default=25, ge=25, le=99)
    mid_range_shot: int = Field(default=25, ge=25, le=99)
    three_point_shot: int = Field(default=25, ge=25, le=99)
    free_throw: int = Field(default=25, ge=25, le=99)
    pass_accuracy: int = Field(default=25, ge=25, le=99)
    ball_handle: int = Field(default=25, ge=25, le=99)
    speed_with_ball: int = Field(default=25, ge=25, le=99)
    interior_defense: int = Field(default=25, ge=25, le=99)
    perimeter_defense: int = Field(default=25, ge=25, le=99)
    steal: int = Field(default=25, ge=25, le=99)
    block: int = Field(default=25, ge=25, le=99)
    offensive_rebound: int = Field(default=25, ge=25, le=99)
    defensive_rebound: int = Field(default=25, ge=25, le=99)
    speed: int = Field(default=25, ge=25, le=99)
    acceleration: int = Field(default=25, ge=25, le=99)
    strength: int = Field(default=25, ge=25, le=99)
    vertical: int = Field(default=25, ge=25, le=99)
    stamina: int = Field(default=25, ge=25, le=99)


class Build(BaseModel):
    """A full NBA 2K26 player build."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Build name (e.g. '6-6 Two-Way Slasher').")
    position: Position
    archetype: Archetype
    height_inches: int = Field(..., ge=66, le=90, description="Height in inches.")
    weight_lbs: int = Field(..., ge=150, le=300, description="Weight in pounds.")
    wingspan_inches: int = Field(..., ge=72, le=96, description="Wingspan in inches.")
    attributes: BuildAttributes
    badges: list[Badge] = Field(default_factory=list)
    overall_rating: int = Field(default=60, ge=60, le=99)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BadgeAllocation(BaseModel):
    """Recommended badge allocation for a build."""

    build_id: UUID
    finishing_badges: list[Badge] = Field(default_factory=list)
    shooting_badges: list[Badge] = Field(default_factory=list)
    playmaking_badges: list[Badge] = Field(default_factory=list)
    defense_badges: list[Badge] = Field(default_factory=list)
    total_badge_points_used: int = Field(default=0, ge=0)
    total_badge_points_available: int = Field(default=0, ge=0)
    optimization_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How optimally badges are allocated (0-1).",
    )


class MetaBuild(BaseModel):
    """A meta build entry — community-ranked build template."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    position: Position
    archetype: Archetype
    meta_tier: MetaTier
    win_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    pick_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How often this build is picked in competitive play.",
    )
    attributes: BuildAttributes
    core_badges: list[Badge] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    counter_builds: list[str] = Field(
        default_factory=list,
        description="Build archetypes that counter this one.",
    )
    patch_version: str = Field(default="1.0", description="Game patch this meta applies to.")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BuildAnalysisResult(BaseModel):
    """Result of a full build analysis."""

    build: Build
    badge_allocation: BadgeAllocation
    attribute_thresholds: list[AttributeThreshold] = Field(default_factory=list)
    meta_tier: MetaTier
    optimization_tips: list[str] = Field(default_factory=list)
    similar_meta_builds: list[MetaBuild] = Field(default_factory=list)


class BuildCompareResult(BaseModel):
    """Head-to-head build comparison."""

    build_a: Build
    build_b: Build
    attribute_advantages_a: dict[str, int] = Field(default_factory=dict)
    attribute_advantages_b: dict[str, int] = Field(default_factory=dict)
    badge_advantage: str = Field(default="even", description="Which build has better badges.")
    matchup_prediction: str = Field(default="", description="Predicted matchup winner.")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
