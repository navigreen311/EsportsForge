"""Pydantic schemas for RankedTours AI + SocietyScout — ranked environment tracking."""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RankedTier(str, enum.Enum):
    """Ranked tier classifications."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    LEGEND = "legend"


class TourType(str, enum.Enum):
    """Tour event types."""

    RANKED_1V1 = "ranked_1v1"
    RANKED_STROKE = "ranked_stroke"
    SOCIETY_EVENT = "society_event"
    SOCIETY_SEASON = "society_season"
    QUALIFIER = "qualifier"
    MAJOR = "major"


class CourseCondition(str, enum.Enum):
    """Course condition presets."""

    STANDARD = "standard"
    FIRM_AND_FAST = "firm_and_fast"
    SOFT = "soft"
    TOURNAMENT = "tournament"
    WINDY = "windy"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class RankedEnvironment(BaseModel):
    """Current ranked environment state."""

    current_tier: RankedTier
    tier_points: int = Field(..., ge=0)
    points_to_next_tier: int = Field(..., ge=0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    avg_score_vs_par: float = Field(
        ..., description="Average score relative to par in ranked play",
    )
    recent_form: list[str] = Field(
        default_factory=list,
        description="Last 5 results, e.g. ['W', 'L', 'W', 'W', 'L']",
    )
    rank_position: Optional[int] = Field(
        None, description="Overall rank position if available",
    )
    streak: int = Field(0, description="Current win/loss streak (positive = wins)")


class TourReport(BaseModel):
    """Analysis of performance in tour/ranked events."""

    tour_type: TourType
    events_played: int = Field(..., ge=0)
    avg_finish: float = Field(..., description="Average finishing position")
    top_3_rate: float = Field(..., ge=0.0, le=1.0)
    scoring_avg: float = Field(..., description="Average score relative to par")
    best_finish: int = Field(..., ge=1)
    worst_finish: int = Field(..., ge=1)
    clutch_rating: float = Field(
        ..., ge=0.0, le=1.0,
        description="Performance in final-round / closing situations",
    )
    course_type_strength: str = Field(
        "", description="Course archetype where player performs best",
    )


class SocietyPrep(BaseModel):
    """Society-specific preparation report."""

    society_name: str
    event_name: str
    course_name: str
    course_condition: CourseCondition
    field_size: int = Field(..., ge=2)
    field_strength: float = Field(
        ..., ge=0.0, le=1.0,
        description="Relative strength of the field",
    )
    recommended_strategy: str = Field(
        ..., description="Overall strategic approach",
    )
    course_notes: list[str] = Field(
        default_factory=list,
        description="Key notes for this course under these conditions",
    )
    scoring_target: float = Field(
        ..., description="Target score to be competitive",
    )
    key_holes: list[int] = Field(
        default_factory=list,
        description="Holes that will make or break the round",
    )
    risk_level: str = Field(
        "moderate", description="Recommended overall risk approach",
    )
    preparation_checklist: list[str] = Field(
        default_factory=list,
        description="Steps to prepare for this event",
    )


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class RankedTrackingRequest(BaseModel):
    """Request for ranked environment analysis."""

    user_id: uuid.UUID
    tour_type: Optional[TourType] = None
    include_history: bool = Field(True, description="Include historical trend data")


class SocietyPrepRequest(BaseModel):
    """Request for society event preparation."""

    user_id: uuid.UUID
    society_name: str = Field(..., min_length=1, max_length=200)
    event_name: str = Field(..., min_length=1, max_length=200)
    course_name: str = Field(..., min_length=1, max_length=200)
    course_condition: CourseCondition = CourseCondition.STANDARD
    field_size: int = Field(20, ge=2)
