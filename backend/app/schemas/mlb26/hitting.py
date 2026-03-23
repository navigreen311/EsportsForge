"""Pydantic schemas for HitForge, BaserunningAI, DiamondDynastyIQ, MLBPlayerTwin."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DecisionType(str, enum.Enum):
    GO = "go"
    HOLD = "hold"
    TAG = "tag"


class PitcherRole(str, enum.Enum):
    STARTER = "starter"
    CLOSER = "closer"
    SETUP = "setup"
    LONG_RELIEF = "long_relief"
    MIDDLE_RELIEF = "middle_relief"
    MATCHUP_LEFTY = "matchup_lefty"


# ---------------------------------------------------------------------------
# Hit timing
# ---------------------------------------------------------------------------

class TimingWindow(BaseModel):
    """Swing timing evaluation result."""
    user_id: str
    pitch_type: str
    swing_ms: float
    optimal_ms: float
    window_ms: float
    offset_ms: float
    grade: str = Field(..., description="perfect, good, okay, miss")
    velo_range: str
    tips: list[str] = Field(default_factory=list)


class PCIPlacement(BaseModel):
    """PCI placement recommendation."""
    user_id: str
    target_zone: int
    pitch_type: str
    pci_x: float = Field(..., ge=0, le=1.0)
    pci_y: float = Field(..., ge=0, le=1.0)
    count: str
    note: str


class CountLeverage(BaseModel):
    """Count leverage analysis."""
    count: str
    leverage: float = Field(..., ge=0, le=1.0)
    approach: str
    recommended_swing_pct: float = Field(..., ge=0, le=1.0)
    advice: list[str] = Field(default_factory=list)


class HitApproach(BaseModel):
    """Recommended hitting approach for a situation."""
    situation: str
    approach: str
    target_zones: list[int] = Field(default_factory=list)
    notes: str


# ---------------------------------------------------------------------------
# Swing feedback
# ---------------------------------------------------------------------------

class SwingFeedback(BaseModel):
    """A single swing attempt record."""
    pitch_type: str
    zone: int = Field(..., ge=1, le=14)
    result: str = Field(..., description="single, double, triple, homer, out, whiff, foul, lineout, flyout, groundout")
    timing_grade: str = Field(..., description="perfect, good, okay, miss")
    pci_accuracy: float = Field(0.5, ge=0, le=1.0)


class SwingResult(BaseModel):
    """Aggregated swing statistics after recording."""
    user_id: str
    total_swings: int
    batting_avg: float
    whiff_rate: float
    perfect_timing_rate: float
    latest_result: str
    latest_grade: str


class HitTrainingPlan(BaseModel):
    """Personalized hitting training plan."""
    user_id: str
    current_avg: float
    target_avg: float
    weak_pitches: list[str] = Field(default_factory=list)
    strong_pitches: list[str] = Field(default_factory=list)
    drills: list[str] = Field(default_factory=list)
    estimated_sessions: int
    focus: str


# ---------------------------------------------------------------------------
# Baserunning
# ---------------------------------------------------------------------------

class StolenBaseAnalysis(BaseModel):
    """Stolen base probability analysis."""
    target_base: str
    success_probability: float = Field(..., ge=0, le=1.0)
    decision: str = Field(..., description="green_light, situational, hold")
    advice: str
    factors: list[str] = Field(default_factory=list)
    runner_speed: int
    catcher_arm: int


class BaserunningDecision(BaseModel):
    """Go/hold decision on a ball in play."""
    decision: DecisionType
    success_probability: float = Field(..., ge=0, le=1.0)
    advice: str
    base_from: str
    outs: int
    run_value: str


class TagUpAnalysis(BaseModel):
    """Tag-up decision on a fly ball."""
    should_tag: bool
    success_probability: float = Field(..., ge=0, le=1.0)
    outfield_depth: str
    fielder_arm: str
    runner_speed: int
    base_from: str
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Diamond Dynasty
# ---------------------------------------------------------------------------

class DDPlayerCard(BaseModel):
    """A Diamond Dynasty player card."""
    name: str
    position: str
    overall: int = Field(..., ge=40, le=99)
    bats: str = Field("R", description="L, R, or S (switch)")
    throws: str = Field("R", description="L or R")
    speed: int = Field(50, ge=0, le=99)
    contact: int = Field(50, ge=0, le=99)
    power: int = Field(50, ge=0, le=99)
    fielding: int = Field(50, ge=0, le=99)
    clutch: int = Field(50, ge=0, le=99)
    velocity: int = Field(0, ge=0, le=99, description="Pitcher only")
    k_per_9: int = Field(0, ge=0, le=99, description="Pitcher only")
    stamina: int = Field(50, ge=0, le=99)
    obp: float = Field(0.0, ge=0, le=1.0, description="Simulated OBP")


class LineupSlot(BaseModel):
    """A slot in the batting order."""
    order: int = Field(..., ge=1, le=9)
    card: DDPlayerCard
    role: str
    fit_score: float


class DDLineup(BaseModel):
    """A complete Diamond Dynasty lineup."""
    slots: list[LineupSlot]
    notes: list[str] = Field(default_factory=list)
    overall_rating: float
    platoon: str = "vs_rhp"


class RotationSlot(BaseModel):
    """A pitching rotation or bullpen slot."""
    card: DDPlayerCard
    role: PitcherRole
    order: int
    notes: str = ""


class DDPitchingStaff(BaseModel):
    """Complete pitching staff configuration."""
    rotation: list[RotationSlot] = Field(default_factory=list)
    bullpen: list[RotationSlot] = Field(default_factory=list)


class StaffAnalysis(BaseModel):
    """Pitching staff analysis result."""
    rotation_avg_ovr: float
    bullpen_avg_ovr: float
    avg_velocity: float
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    overall_grade: str


# ---------------------------------------------------------------------------
# Player Twin
# ---------------------------------------------------------------------------

class PitchRecognition(BaseModel):
    """Pitch recognition evaluation."""
    user_id: str
    sample_size: int
    overall_grade: str
    chase_rate: float
    take_rate_on_balls: float
    pitch_type_recognition: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class ZoneProfile(BaseModel):
    """9-zone hitting profile."""
    user_id: str
    zones: dict[int, dict[str, float]] = Field(default_factory=dict)
    hot_zones: list[int] = Field(default_factory=list)
    cold_zones: list[int] = Field(default_factory=list)
    sample_size: int
    recommendation: str


class ClutchProfile(BaseModel):
    """Clutch RISP performance analysis."""
    user_id: str
    risp_avg: float
    non_risp_avg: float
    clutch_diff: float
    late_close_avg: float
    grade: str = Field(..., description="clutch, steady, developing, chokes_under_pressure")
    risp_sample: int
    notes: list[str] = Field(default_factory=list)


class ZoneHittingProfile(BaseModel):
    """Zone hitting optimization profile."""
    user_id: str
    zones: dict[int, dict[str, float]] = Field(default_factory=dict)
    recommended_zones: list[int] = Field(default_factory=list)


class MLBTwinProfile(BaseModel):
    """Complete MLB The Show 26 player twin profile."""
    user_id: str
    pitch_recognition: PitchRecognition
    zone_profile: ZoneProfile
    clutch: ClutchProfile
    at_bats_analyzed: int = 0
