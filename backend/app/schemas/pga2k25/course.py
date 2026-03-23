"""Pydantic schemas for CourseIQ — per-hole strategy, line EV, hazard risk."""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HazardType(str, enum.Enum):
    """Course hazard classifications."""

    WATER = "water"
    BUNKER = "bunker"
    DEEP_ROUGH = "deep_rough"
    OB = "out_of_bounds"
    TREES = "trees"
    FAIRWAY_BUNKER = "fairway_bunker"
    WASTE_AREA = "waste_area"


class ShotShape(str, enum.Enum):
    """Shot shape options."""

    STRAIGHT = "straight"
    FADE = "fade"
    DRAW = "draw"
    HIGH = "high"
    LOW = "low"
    PUNCH = "punch"


class LineType(str, enum.Enum):
    """Approach line classification."""

    AGGRESSIVE = "aggressive"
    SAFE = "safe"
    LAYUP = "layup"
    RECOVERY = "recovery"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class HazardRisk(BaseModel):
    """Risk assessment for a specific hazard on a hole."""

    hazard_type: HazardType
    location: str = Field(..., description="e.g. 'left side at 250y', 'greenside right'")
    probability: float = Field(
        ..., ge=0.0, le=1.0,
        description="Probability of finding this hazard on the aggressive line",
    )
    penalty_strokes: float = Field(
        ..., description="Expected stroke penalty if the hazard is hit",
    )
    avoidance_strategy: str = Field(
        ..., description="How to avoid this hazard",
    )


class LineEV(BaseModel):
    """Expected value comparison for safe vs aggressive line."""

    line_type: LineType
    expected_score: float = Field(..., description="Expected strokes for this line")
    birdie_probability: float = Field(0.0, ge=0.0, le=1.0)
    par_probability: float = Field(0.0, ge=0.0, le=1.0)
    bogey_probability: float = Field(0.0, ge=0.0, le=1.0)
    double_or_worse_probability: float = Field(0.0, ge=0.0, le=1.0)
    risk_reward_ratio: float = Field(
        ..., description="Birdie gain vs bogey+ risk ratio",
    )
    recommended: bool = Field(
        False, description="Whether this line is recommended given the player profile",
    )


class ShotPlan(BaseModel):
    """Planned shot for a hole segment."""

    shot_number: int
    club: str
    target_distance: float = Field(..., description="Target distance in yards")
    shot_shape: ShotShape = ShotShape.STRAIGHT
    aim_point: str = Field(..., description="Where to aim, e.g. 'center fairway'")
    notes: Optional[str] = None


class HoleStrategy(BaseModel):
    """Complete strategy for a single hole."""

    hole_number: int = Field(..., ge=1, le=18)
    par: int = Field(..., ge=3, le=5)
    yardage: int
    handicap_index: int = Field(..., ge=1, le=18, description="Hole difficulty rank")
    hazards: list[HazardRisk] = Field(default_factory=list)
    line_options: list[LineEV] = Field(default_factory=list)
    recommended_line: LineType = LineType.SAFE
    shot_plan: list[ShotPlan] = Field(default_factory=list)
    bogey_avoidance_notes: str = Field(
        "", description="Key notes for avoiding bogey on this hole",
    )
    key_miss: str = Field(
        "", description="The miss to avoid at all costs",
    )


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class CourseAnalysisRequest(BaseModel):
    """Request to analyze a course."""

    user_id: uuid.UUID
    course_name: str = Field(..., min_length=1, max_length=200)
    tee_box: str = Field("championship", description="Tee box selection")
    player_handicap: float = Field(0.0, description="In-game handicap / skill index")
    risk_tolerance: float = Field(
        0.5, ge=0.0, le=1.0,
        description="0=ultra-conservative, 1=full send",
    )
    session_history_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="Previous session IDs for personalized strategy",
    )


class CourseAnalysis(BaseModel):
    """Full course analysis output."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    course_name: str
    tee_box: str
    total_yardage: int
    par: int
    holes: list[HoleStrategy]
    overall_strategy: str = Field(
        ..., description="High-level round strategy summary",
    )
    target_score: float = Field(
        ..., description="Projected score with recommended strategy",
    )
    bogey_danger_holes: list[int] = Field(
        default_factory=list,
        description="Hole numbers where bogey risk is highest",
    )
    birdie_opportunity_holes: list[int] = Field(
        default_factory=list,
        description="Hole numbers with best birdie EV",
    )
    risk_management_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="How well the strategy minimizes downside risk",
    )
    confidence: float = Field(0.75, ge=0.0, le=1.0)
    generated_at: str = ""
