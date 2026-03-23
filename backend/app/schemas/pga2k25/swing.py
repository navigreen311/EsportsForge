"""Pydantic schemas for SwingForge Golf — swing diagnosis, miss profiles, pressure drift."""

from __future__ import annotations

import enum
import uuid
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SwingSystem(str, enum.Enum):
    """PGA 2K25 swing mechanic systems."""

    EVOSWING = "evoswing"
    SWING_STICK = "swing_stick"
    THREE_CLICK = "three_click"


class FaultSeverity(str, enum.Enum):
    """How critical a swing fault is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MissDirection(str, enum.Enum):
    """Direction of miss tendency."""

    LEFT = "left"
    RIGHT = "right"
    SHORT = "short"
    LONG = "long"
    FAT = "fat"
    THIN = "thin"


class ClubCategory(str, enum.Enum):
    """Club groupings for miss profile analysis."""

    DRIVER = "driver"
    FAIRWAY_WOOD = "fairway_wood"
    HYBRID = "hybrid"
    LONG_IRON = "long_iron"
    MID_IRON = "mid_iron"
    SHORT_IRON = "short_iron"
    WEDGE = "wedge"
    PUTTER = "putter"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class SwingFault(BaseModel):
    """A diagnosed swing fault."""

    fault_name: str = Field(..., description="e.g. 'early release', 'casting', 'over-rotation'")
    severity: FaultSeverity
    affected_clubs: list[ClubCategory] = Field(default_factory=list)
    description: str
    correction: str = Field(..., description="Recommended fix")
    drill_name: Optional[str] = Field(None, description="Specific drill to address this fault")


class ClubMissProfile(BaseModel):
    """Miss pattern for a specific club category."""

    club_category: ClubCategory
    primary_miss: MissDirection
    secondary_miss: Optional[MissDirection] = None
    miss_frequency: float = Field(
        ..., ge=0.0, le=1.0,
        description="How often a miss occurs (0=never, 1=every shot)",
    )
    average_miss_distance: float = Field(
        ..., description="Average offline distance in yards",
    )
    consistency_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="1.0 = tight dispersion, 0.0 = wild",
    )
    notes: str = ""


class PressureDrift(BaseModel):
    """How swing changes under pressure situations."""

    situation: str = Field(
        ..., description="e.g. 'tournament final holes', 'tight match', 'leader board pressure'",
    )
    tempo_change: float = Field(
        ..., description="Tempo deviation from baseline (negative = faster)",
    )
    miss_direction_shift: Optional[MissDirection] = Field(
        None, description="Where misses tend to go under pressure",
    )
    accuracy_drop: float = Field(
        ..., ge=0.0, le=1.0,
        description="Percentage accuracy loss under pressure",
    )
    mitigation: str = Field(
        ..., description="Strategy to counteract pressure drift",
    )


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class SwingDiagnosisRequest(BaseModel):
    """Request to diagnose swing faults."""

    user_id: uuid.UUID
    swing_system: SwingSystem = SwingSystem.EVOSWING
    session_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="Session IDs to analyze for swing data",
    )
    include_pressure: bool = Field(
        True, description="Include pressure drift analysis",
    )


class SwingDiagnosis(BaseModel):
    """Complete swing diagnosis output."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID
    swing_system: SwingSystem
    faults: list[SwingFault] = Field(default_factory=list)
    club_profiles: list[ClubMissProfile] = Field(default_factory=list)
    pressure_drift: list[PressureDrift] = Field(default_factory=list)
    overall_consistency: float = Field(
        ..., ge=0.0, le=1.0,
        description="Aggregate consistency across all clubs",
    )
    tempo_rating: float = Field(
        ..., ge=0.0, le=1.0,
        description="How consistent the swing tempo is",
    )
    priority_fix: Optional[str] = Field(
        None, description="Single most impactful thing to fix",
    )
    confidence: float = Field(0.75, ge=0.0, le=1.0)
    generated_at: str = ""
