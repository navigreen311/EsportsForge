"""Pydantic schemas for Dispersion Maps — real miss patterns per club from session history."""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class SessionShot(BaseModel):
    """A single shot record from a session."""

    session_id: uuid.UUID
    hole_number: int = Field(..., ge=1, le=18)
    shot_number: int = Field(..., ge=1)
    club: str
    intended_distance: float
    actual_distance: float
    offline_yards: float = Field(
        ..., description="Lateral miss in yards (negative = left, positive = right)",
    )
    long_short_yards: float = Field(
        ..., description="Distance miss in yards (negative = short, positive = long)",
    )
    lie: str = Field("fairway")
    wind_speed: float = Field(0.0)
    pressure_situation: bool = Field(False)


class MissPattern(BaseModel):
    """Aggregated miss pattern for a club."""

    avg_offline: float = Field(
        ..., description="Average lateral miss in yards",
    )
    avg_long_short: float = Field(
        ..., description="Average distance miss in yards",
    )
    std_offline: float = Field(
        ..., description="Standard deviation of lateral misses",
    )
    std_long_short: float = Field(
        ..., description="Standard deviation of distance misses",
    )
    left_miss_pct: float = Field(..., ge=0.0, le=1.0)
    right_miss_pct: float = Field(..., ge=0.0, le=1.0)
    short_miss_pct: float = Field(..., ge=0.0, le=1.0)
    long_miss_pct: float = Field(..., ge=0.0, le=1.0)
    total_shots: int = Field(..., ge=0)


class ClubDispersion(BaseModel):
    """Dispersion data for a single club."""

    club: str
    avg_carry: float = Field(..., description="Average carry distance")
    avg_total: float = Field(..., description="Average total distance")
    miss_pattern: MissPattern
    dispersion_radius_yards: float = Field(
        ..., description="Circle radius that contains 68% of shots",
    )
    dispersion_area_sq_yards: float = Field(
        ..., description="Ellipse area of the dispersion pattern",
    )
    consistency_grade: str = Field(
        ..., description="A+ through F grade for consistency",
    )
    pressure_dispersion_multiplier: float = Field(
        1.0, description="How much dispersion increases under pressure",
    )
    notes: str = ""


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class DispersionMapRequest(BaseModel):
    """Request to build a dispersion map."""

    user_id: uuid.UUID
    session_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="Sessions to analyze; empty = all available",
    )
    clubs: list[str] = Field(
        default_factory=list,
        description="Specific clubs to analyze; empty = all clubs",
    )
    min_shots_per_club: int = Field(
        5, ge=1,
        description="Minimum shots required for a club to be included",
    )


class DispersionMap(BaseModel):
    """Complete dispersion map across all clubs."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    clubs: list[ClubDispersion] = Field(default_factory=list)
    total_shots_analyzed: int = Field(0, ge=0)
    most_consistent_club: Optional[str] = None
    least_consistent_club: Optional[str] = None
    overall_dispersion_grade: str = Field(
        "C", description="Overall grade across all clubs",
    )
    improvement_priority: Optional[str] = Field(
        None, description="Club that would benefit most from practice",
    )
    confidence: float = Field(0.75, ge=0.0, le=1.0)
    generated_at: str = ""
