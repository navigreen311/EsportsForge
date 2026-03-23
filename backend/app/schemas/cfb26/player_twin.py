"""CFB PlayerTwin schemas — trick play readiness, option defense profiles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TrickPlayType(str, Enum):
    """Types of trick plays."""

    FAKE_PUNT = "fake_punt"
    FAKE_FIELD_GOAL = "fake_field_goal"
    FLEA_FLICKER = "flea_flicker"
    HOOK_AND_LATERAL = "hook_and_lateral"
    DOUBLE_PASS = "double_pass"
    PHILLY_SPECIAL = "philly_special"
    WILDCAT = "wildcat"
    STATUE_OF_LIBERTY = "statue_of_liberty"
    REVERSE = "reverse"
    HALFBACK_PASS = "halfback_pass"


class OptionType(str, Enum):
    """Types of option plays to defend."""

    TRIPLE_OPTION = "triple_option"
    ZONE_READ = "zone_read"
    SPEED_OPTION = "speed_option"
    VEER = "veer"
    MIDLINE = "midline"
    INVERTED_VEER = "inverted_veer"
    RPO = "rpo"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class TrickPlayReadiness(BaseModel):
    """Readiness assessment for a specific trick play type."""

    play_type: TrickPlayType
    recognition_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="How often the user recognizes this trick play (0-1).",
    )
    reaction_speed: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Speed of reaction once recognized (0=slow, 1=instant).",
    )
    success_rate_against: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How often user successfully defends this play.",
    )
    times_faced: int = Field(default=0, ge=0)
    times_burned: int = Field(default=0, ge=0)
    key_tells: list[str] = Field(
        default_factory=list,
        description="Pre-snap tells that indicate this trick play.",
    )


class TrickPlayProfile(BaseModel):
    """Overall trick play recognition profile for a user."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    overall_readiness: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall trick play readiness score.",
    )
    play_readiness: list[TrickPlayReadiness] = Field(default_factory=list)
    biggest_vulnerability: TrickPlayType | None = None
    recommended_drills: list[str] = Field(default_factory=list)
    games_analyzed: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OptionAssignment(BaseModel):
    """How well the user handles a specific option assignment."""

    option_type: OptionType
    assignment_discipline: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well user stays in assignment (0=freelances, 1=disciplined).",
    )
    read_accuracy: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well user reads the option (0=wrong, 1=perfect).",
    )
    contain_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="How often user contains the QB/RB.",
    )
    yards_allowed_per_attempt: float = Field(
        default=0.0, ge=0.0,
        description="Average yards allowed when facing this option.",
    )
    times_faced: int = Field(default=0, ge=0)


class OptionDefenseProfile(BaseModel):
    """Overall option defense profile for a user."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    overall_option_defense: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall option defense score.",
    )
    assignments: list[OptionAssignment] = Field(default_factory=list)
    worst_option_type: OptionType | None = None
    common_mistakes: list[str] = Field(default_factory=list)
    recommended_adjustments: list[str] = Field(default_factory=list)
    games_analyzed: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class PlayerTwinResponse(BaseModel):
    """Envelope for CFB player twin endpoints."""

    user_id: str
    trick_play_profile: TrickPlayProfile | None = None
    option_defense_profile: OptionDefenseProfile | None = None
