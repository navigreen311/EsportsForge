"""HomeField Advantage Manager schemas — crowd noise and snap protocols."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class NoiseLevel(str, Enum):
    """Stadium noise intensity classification."""

    QUIET = "quiet"
    MODERATE = "moderate"
    LOUD = "loud"
    DEAFENING = "deafening"
    EARTHQUAKE = "earthquake"


class StadiumTier(str, Enum):
    """Stadium atmosphere tier based on program prestige and capacity."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ELITE = "elite"
    LEGENDARY = "legendary"


# ---------------------------------------------------------------------------
# Core value objects
# ---------------------------------------------------------------------------

class SnapProtocol(BaseModel):
    """Adjusted snap count protocol for crowd noise."""

    noise_level: NoiseLevel
    recommended_snap_count: str = Field(
        ..., description="Recommended snap count type (e.g. 'silent', 'leg_tap', 'wrist_clap').",
    )
    cadence_type: str = Field(
        default="silent",
        description="Cadence: silent, quick, normal, hard_count.",
    )
    pre_snap_motion: bool = Field(
        default=False,
        description="Whether to use pre-snap motion to draw offsides.",
    )
    false_start_risk: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Estimated false start risk at this noise level.",
    )
    hard_count_effectiveness: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How effective hard counts are at this noise level.",
    )
    tips: list[str] = Field(
        default_factory=list,
        description="Practical tips for handling this noise level.",
    )


class CrowdAdjustment(BaseModel):
    """Overall adjustments for home/away crowd effects."""

    is_home: bool
    stadium: str = Field(default="")
    stadium_tier: StadiumTier = Field(default=StadiumTier.MEDIUM)
    noise_level: NoiseLevel
    crowd_intensity: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Current crowd intensity factor.",
    )
    offensive_adjustments: list[str] = Field(
        default_factory=list,
        description="Adjustments to make on offense.",
    )
    defensive_adjustments: list[str] = Field(
        default_factory=list,
        description="Adjustments to make on defense.",
    )
    momentum_multiplier: float = Field(
        default=1.0, ge=0.5, le=2.0,
        description="Crowd multiplier on momentum effects.",
    )
    opponent_penalty_boost: float = Field(
        default=0.0, ge=0.0, le=0.5,
        description="Boost to opponent penalty likelihood from crowd.",
    )
    snap_protocol: SnapProtocol | None = None


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class HomeFieldInput(BaseModel):
    """Input for home field advantage calculations."""

    home_away: str = Field(
        ..., description="'home' or 'away'.",
    )
    stadium: str = Field(default="")
    opponent: str = Field(default="")
    stadium_capacity: int = Field(default=50000, ge=0)
    rivalry_game: bool = Field(default=False)
    night_game: bool = Field(default=False)
    weather: str = Field(default="clear")
    conference_game: bool = Field(default=True)


class HomeFieldResponse(BaseModel):
    """Envelope for home field endpoints."""

    adjustment: CrowdAdjustment
    snap_protocol: SnapProtocol
