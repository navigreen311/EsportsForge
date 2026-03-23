"""Pydantic schemas for WindLine AI — wind-adjusted club selection, trajectory control."""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WindDirection(str, enum.Enum):
    """Cardinal and ordinal wind directions."""

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"
    HEADWIND = "headwind"
    TAILWIND = "tailwind"
    CROSSWIND_LEFT = "crosswind_left"
    CROSSWIND_RIGHT = "crosswind_right"


class TrajectoryType(str, enum.Enum):
    """Ball flight trajectory options."""

    HIGH = "high"
    MID = "mid"
    LOW = "low"
    STINGER = "stinger"
    FLIGHTED = "flighted"


class ShotConfidence(str, enum.Enum):
    """Confidence level in executing the wind-adjusted shot."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    RISKY = "risky"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class WindCondition(BaseModel):
    """Current wind state."""

    speed_mph: float = Field(..., ge=0.0, le=50.0)
    direction: WindDirection
    gusting: bool = Field(False, description="Whether wind is gusting")
    gust_speed_mph: Optional[float] = Field(None, ge=0.0, le=60.0)
    elevation_factor: float = Field(
        1.0, description="Multiplier for elevation effect on wind",
    )


class CarryTotalSplit(BaseModel):
    """Carry distance vs total distance breakdown."""

    carry_yards: float = Field(..., description="Carry distance in yards")
    total_yards: float = Field(..., description="Total distance including roll")
    roll_yards: float = Field(..., description="Expected roll after landing")
    wind_carry_adjustment: float = Field(
        ..., description="Yards added/subtracted by wind to carry",
    )
    wind_total_adjustment: float = Field(
        ..., description="Yards added/subtracted by wind to total",
    )


class TrajectoryControl(BaseModel):
    """Recommended trajectory for wind conditions."""

    trajectory: TrajectoryType
    reason: str = Field(..., description="Why this trajectory is recommended")
    apex_height: str = Field(
        ..., description="Relative apex, e.g. 'low', 'standard', 'high'",
    )
    wind_exposure: float = Field(
        ..., ge=0.0, le=1.0,
        description="0=minimal wind effect, 1=maximum wind effect",
    )
    spin_adjustment: Optional[str] = Field(
        None, description="Spin change recommendation",
    )


class WindAdjustedSelection(BaseModel):
    """Complete wind-adjusted club selection."""

    original_club: str = Field(..., description="Club for this distance with no wind")
    adjusted_club: str = Field(..., description="Club after wind adjustment")
    original_distance: float = Field(..., description="Target distance in yards")
    wind_adjusted_distance: float = Field(
        ..., description="Effective distance accounting for wind",
    )
    carry_total: CarryTotalSplit
    trajectory: TrajectoryControl
    aim_adjustment: str = Field(
        ..., description="e.g. '10 yards left of target to account for crosswind'",
    )
    confidence: ShotConfidence
    notes: str = ""


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class WindSelectionRequest(BaseModel):
    """Request for wind-adjusted club selection."""

    user_id: uuid.UUID
    target_distance: float = Field(..., gt=0, description="Desired distance in yards")
    wind: WindCondition
    lie: str = Field("fairway", description="Current lie: fairway, rough, tee, etc.")
    elevation_change: float = Field(
        0.0, description="Elevation change to target in feet",
    )
    club_preference: Optional[str] = Field(
        None, description="Player's preferred club for this distance",
    )
