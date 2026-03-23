"""Pydantic schemas for GreenIQ — read quality, pace control, three-putt risk."""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GreenSpeed(str, enum.Enum):
    """Green speed classifications (stimpmeter)."""

    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    TOURNAMENT = "tournament"


class SlopeDirection(str, enum.Enum):
    """General slope/break direction."""

    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    UPHILL = "uphill"
    DOWNHILL = "downhill"
    DOUBLE_BREAK = "double_break"
    FLAT = "flat"


class PuttDifficulty(str, enum.Enum):
    """Putt difficulty classification."""

    TAP_IN = "tap_in"
    MAKEABLE = "makeable"
    CHALLENGING = "challenging"
    LAG = "lag"
    HEROIC = "heroic"


class PressurePuttingMode(str, enum.Enum):
    """Putting strategy modes under pressure."""

    AGGRESSIVE = "aggressive"
    SAFE_TWO_PUTT = "safe_two_putt"
    LAG_AND_TAP = "lag_and_tap"
    DIE_IN_HOLE = "die_in_hole"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PaceControl(BaseModel):
    """Pace / speed control analysis for a putt."""

    recommended_power: float = Field(
        ..., ge=0.0, le=100.0,
        description="Power percentage for the putt (0-100)",
    )
    leave_distance: float = Field(
        ..., description="Expected distance past the hole in feet if missed",
    )
    comeback_difficulty: PuttDifficulty = Field(
        PuttDifficulty.TAP_IN,
        description="Difficulty of the comeback putt if this one misses",
    )
    speed_tolerance: float = Field(
        ..., description="Acceptable power variance window (+/- percent)",
    )


class ThreePuttRisk(BaseModel):
    """Three-putt probability assessment."""

    probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probability of three-putting",
    )
    risk_level: str = Field(..., description="low / medium / high / extreme")
    primary_cause: str = Field(
        ..., description="Most likely cause, e.g. 'pace misjudgment', 'poor read'",
    )
    mitigation: str = Field(
        ..., description="Strategy to reduce three-putt risk",
    )


class GreenRead(BaseModel):
    """Detailed read for a single putt."""

    distance_feet: float = Field(..., gt=0)
    slope_direction: SlopeDirection
    break_amount: float = Field(
        ..., description="Break amount in inches at the target pace",
    )
    elevation_change: float = Field(
        0.0, description="Elevation change in feet (positive = uphill)",
    )
    aim_point: str = Field(
        ..., description="Where to aim, e.g. '2 cups left edge'",
    )
    grain_effect: Optional[str] = Field(
        None, description="Grain influence on the putt if applicable",
    )


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class GreenReadRequest(BaseModel):
    """Request for green reading analysis."""

    user_id: uuid.UUID
    course_name: str = Field(..., min_length=1, max_length=200)
    hole_number: int = Field(..., ge=1, le=18)
    pin_position: str = Field("center", description="Pin position on the green")
    distance_feet: float = Field(..., gt=0, description="Distance to the hole in feet")
    green_speed: GreenSpeed = GreenSpeed.MEDIUM
    include_pressure: bool = Field(
        True, description="Include pressure putting recommendations",
    )


class PuttAnalysis(BaseModel):
    """Complete putting analysis for a green."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    hole_number: int
    course_name: str
    green_speed: GreenSpeed
    read: GreenRead
    pace: PaceControl
    three_putt_risk: ThreePuttRisk
    difficulty: PuttDifficulty
    make_probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probability of making the putt",
    )
    pressure_mode: PressurePuttingMode = PressurePuttingMode.SAFE_TWO_PUTT
    pressure_adjustment: Optional[str] = Field(
        None, description="How to adjust under pressure",
    )
    read_quality_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence in the read accuracy",
    )
    confidence: float = Field(0.75, ge=0.0, le=1.0)
    generated_at: str = ""
