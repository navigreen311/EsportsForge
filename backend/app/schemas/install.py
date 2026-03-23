"""InstallAI & ProgressionOS schemas — install packages and mastery progression."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MasteryPhase(str, Enum):
    """Phased mastery progression — each phase builds on the last."""

    BASE = "base"
    PRESSURE = "pressure"
    ANTI_META = "anti_meta"
    TOURNAMENT = "tournament"


class InstallStatus(str, Enum):
    """Current status of an install item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    MASTERED = "mastered"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# InstallAI value objects
# ---------------------------------------------------------------------------

class AudibleLayer(BaseModel):
    """Single layer in the three-layer audible tree."""

    condition: str = Field(..., description="The read or trigger condition.")
    action: str = Field(..., description="What to audible to / what to do.")
    notes: str = Field(default="", description="Coaching notes for this layer.")


class AudibleTree(BaseModel):
    """Three-layer if-then decision tree: base call -> if bagged -> if they adjust."""

    id: UUID = Field(default_factory=uuid4)
    base_play: str = Field(..., description="The base play call.")
    base_call: AudibleLayer = Field(..., description="Layer 1: base read and action.")
    if_bagged: AudibleLayer = Field(
        ...,
        description="Layer 2: what to do if the base call is taken away.",
    )
    if_they_adjust: AudibleLayer = Field(
        ...,
        description="Layer 3: counter-adjustment if opponent adapts to layer 2.",
    )


class CallSheet(BaseModel):
    """Formatted call sheet derived from a gameplan."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Game title (e.g. 'madden26').")
    situation_groups: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Situation label -> list of play calls. E.g. '1st_and_10': ['HB Dive', 'PA Boot'].",
    )
    red_zone_calls: list[str] = Field(default_factory=list)
    two_minute_calls: list[str] = Field(default_factory=list)
    audibles: list[AudibleTree] = Field(default_factory=list)
    notes: str = Field(default="", description="Overall coaching notes.")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MiniEBook(BaseModel):
    """Condensed learning document for a single concept."""

    id: UUID = Field(default_factory=uuid4)
    topic: str = Field(..., description="The concept being taught.")
    summary: str = Field(..., description="One-paragraph executive summary.")
    sections: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of {heading, content} pairs.",
    )
    key_takeaways: list[str] = Field(default_factory=list)
    practice_drills: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RedZonePackage(BaseModel):
    """Red zone specific install — scoring-area plays and reads."""

    id: UUID = Field(default_factory=uuid4)
    formations: list[str] = Field(default_factory=list)
    plays: list[str] = Field(default_factory=list)
    reads: list[AudibleTree] = Field(
        default_factory=list,
        description="Audible trees specific to red zone situations.",
    )
    goal_line_package: list[str] = Field(default_factory=list)
    fade_routes: list[str] = Field(default_factory=list)
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AntiBlitzScript(BaseModel):
    """Anti-blitz specific install — pressure beaters and hot routes."""

    id: UUID = Field(default_factory=uuid4)
    blitz_type: str = Field(..., description="Type of blitz this counters.")
    hot_routes: list[str] = Field(default_factory=list)
    quick_passes: list[str] = Field(default_factory=list)
    protection_adjustments: list[str] = Field(default_factory=list)
    audible_tree: AudibleTree | None = None
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InstallPackage(BaseModel):
    """Complete install package — everything a player needs to execute a gameplan."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    title: str = Field(..., description="Game title (e.g. 'madden26').")
    opponent: str = Field(default="", description="Opponent identifier if applicable.")
    call_sheet: CallSheet
    ebook: MiniEBook
    audible_trees: list[AudibleTree] = Field(default_factory=list)
    red_zone_package: RedZonePackage
    anti_blitz_scripts: list[AntiBlitzScript] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ProgressionOS value objects
# ---------------------------------------------------------------------------

class ProgressionStep(BaseModel):
    """A single step in the mastery progression."""

    id: UUID = Field(default_factory=uuid4)
    label: str = Field(..., description="What to learn or practice.")
    description: str = Field(default="")
    phase: MasteryPhase
    impact_rank_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="ImpactRank priority score driving this step.",
    )
    status: InstallStatus = InstallStatus.PENDING
    estimated_hours: float = Field(default=1.0, gt=0.0)
    order: int = Field(default=1, ge=1, description="Sequence within the phase.")


class PhaseProgress(BaseModel):
    """Progress within a single mastery phase."""

    phase: MasteryPhase
    total_steps: int = 0
    completed_steps: int = 0
    mastery_pct: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Percent complete."
    )
    is_current: bool = False
    is_unlocked: bool = False


class WeeklyRoadmap(BaseModel):
    """ImpactRank-driven weekly install plan."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    title: str = Field(..., description="Game title.")
    week_number: int = Field(..., ge=1)
    current_phase: MasteryPhase
    steps: list[ProgressionStep] = Field(default_factory=list)
    total_estimated_hours: float = Field(default=0.0, ge=0.0)
    max_hours_per_week: float = Field(
        default=10.0,
        gt=0.0,
        description="Overload throttle — max hours to install per week.",
    )
    is_overloaded: bool = Field(
        default=False,
        description="True if throttling was applied to prevent overload.",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OverloadCheck(BaseModel):
    """Result of an overload check."""

    user_id: str
    is_overloaded: bool
    active_installs: int
    active_hours: float
    max_hours: float
    recommendation: str = Field(
        default="",
        description="Throttling recommendation if overloaded.",
    )


# ---------------------------------------------------------------------------
# API request / response helpers
# ---------------------------------------------------------------------------

class InstallRequest(BaseModel):
    """Request body for generating installs."""

    user_id: str
    title: str = Field(..., description="Game title (e.g. 'madden26').")
    gameplan: dict = Field(default_factory=dict, description="Gameplan data to convert.")
    player_profile: dict = Field(default_factory=dict, description="Player twin data.")
    opponent: str = Field(default="", description="Opponent identifier.")


class CallSheetRequest(BaseModel):
    """Request body for generating a call sheet only."""

    user_id: str
    title: str
    gameplan: dict = Field(default_factory=dict)
    player_profile: dict = Field(default_factory=dict)


class ProgressionConfig(BaseModel):
    """Configuration for progression system."""

    user_id: str
    title: str
    max_hours_per_week: float = Field(default=10.0, gt=0.0)
    max_active_installs: int = Field(default=5, ge=1, le=20)
    auto_advance: bool = Field(
        default=True,
        description="Auto-advance to next phase when current is mastered.",
    )
