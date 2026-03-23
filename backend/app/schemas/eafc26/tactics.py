"""Pydantic schemas for TacticsForge, SkillForge, and SetPieceForge in EA FC 26."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FormationRating(str, enum.Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class FormationTrend(str, enum.Enum):
    RISING = "rising"
    STABLE = "stable"
    DECLINING = "declining"


class SkillRating(str, enum.Enum):
    OPTIMAL = "optimal"
    EFFECTIVE = "effective"
    SITUATIONAL = "situational"
    AVOID = "avoid"


class TimingGrade(str, enum.Enum):
    PERFECT = "perfect"
    GOOD = "good"
    OKAY = "okay"
    MISTIMED = "mistimed"


class DeliveryType(str, enum.Enum):
    INSWINGER = "inswinger"
    OUTSWINGER = "outswinger"
    SHORT = "short"
    DRIVEN = "driven"


class PenaltyDirection(str, enum.Enum):
    LEFT_LOW = "left_low"
    LEFT_MID = "left_mid"
    LEFT_HIGH = "left_high"
    CENTER_LOW = "center_low"
    CENTER_MID = "center_mid"
    CENTER_HIGH = "center_high"
    RIGHT_LOW = "right_low"
    RIGHT_MID = "right_mid"
    RIGHT_HIGH = "right_high"


# ---------------------------------------------------------------------------
# Tactics schemas
# ---------------------------------------------------------------------------

class FormationMeta(BaseModel):
    """Formation meta snapshot."""
    name: str
    rating: FormationRating
    trend: FormationTrend
    usage_pct: float = Field(..., ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    best_playstyle: str


class TacticalReport(BaseModel):
    """Full tactical meta report."""
    patch_version: str
    report_date: str
    formations: list[FormationMeta]
    top_formation: str
    meta_summary: str


class CounterTactic(BaseModel):
    """Counter-tactic for a specific opponent formation."""
    opponent_formation: str
    recommended_formation: str
    key_adjustments: list[str] = Field(default_factory=list)
    player_instructions: list[str] = Field(default_factory=list)
    critical_moment: str
    confidence: float = Field(..., ge=0, le=1.0)


class InstructionPreset(BaseModel):
    """Custom tactical instruction preset."""
    name: str
    description: str
    build_up: str
    chance_creation: str
    defence: str
    width: int = Field(..., ge=1, le=100)
    depth: int = Field(..., ge=1, le=100)
    players_in_box: int = Field(..., ge=1, le=10)
    corners: str = "Default"
    free_kicks: str = "Default"


class CustomInstruction(BaseModel):
    """Optimized custom instruction output."""
    formation: str
    preset_name: str
    build_up: str
    chance_creation: str
    defence: str
    width: int
    depth: int
    players_in_box: int
    corners: str
    free_kicks: str
    adjustments: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Skill move schemas
# ---------------------------------------------------------------------------

class SkillMoveData(BaseModel):
    """Raw skill move data."""
    name: str
    star_rating: int = Field(..., ge=1, le=5)
    input_window_ms: float
    recovery_frames: int
    effectiveness: dict[str, float] = Field(default_factory=dict)
    best_situations: list[str] = Field(default_factory=list)
    input_sequence: str


class SkillMoveAnalysis(BaseModel):
    """Analysis result for a specific skill move."""
    skill_name: str
    available: bool
    effectiveness: float = Field(..., ge=0, le=1.0)
    rating: SkillRating
    reason: str
    input_sequence: str | None = None
    recovery_frames: int | None = None
    alternatives: list[str] = Field(default_factory=list)


class InputTimingResult(BaseModel):
    """Timing evaluation for a skill move input attempt."""
    user_id: str
    skill_name: str
    input_ms: float
    optimal_ms: float
    offset_ms: float
    grade: TimingGrade
    tips: list[str] = Field(default_factory=list)


class SkillChain(BaseModel):
    """A recommended two-move skill chain."""
    name: str
    moves: list[str]
    combined_effectiveness: float = Field(..., ge=0, le=1.0)
    situation: str
    difficulty: float = Field(..., ge=0, le=1.0)


class SkillTrainingPlan(BaseModel):
    """Personalized skill training plan."""
    user_id: str
    total_attempts: int
    weak_skills: list[str] = Field(default_factory=list)
    strong_skills: list[str] = Field(default_factory=list)
    drills: list[str] = Field(default_factory=list)
    estimated_sessions: int
    focus_tip: str


# ---------------------------------------------------------------------------
# Set piece schemas
# ---------------------------------------------------------------------------

class CornerRoutine(BaseModel):
    """Corner kick routine configuration."""
    name: str
    delivery: DeliveryType
    target_zone: str
    runners: list[str] = Field(default_factory=list)
    success_rate: float = Field(..., ge=0, le=1.0)
    description: str
    counter_tip: str
    opponent_marking: str | None = None


class FreeKickSetup(BaseModel):
    """Free kick technique optimization."""
    distance_yards: float
    zone: str
    optimal_power: float
    curve_amount: str
    aim_offset: str
    technique: str
    success_rate: float = Field(..., ge=0, le=1.0)
    wall_size: int
    tip: str


class PenaltyAnalysis(BaseModel):
    """Penalty kick direction analysis under pressure."""
    recommended_direction: PenaltyDirection
    score_probability: float = Field(..., ge=0, le=1.0)
    alternative_direction: PenaltyDirection
    alternative_probability: float
    ev_by_direction: dict[PenaltyDirection, float] = Field(default_factory=dict)
    pressure_level: str
    composure_factor: float
    advice: list[str] = Field(default_factory=list)


class SetPieceReport(BaseModel):
    """Comprehensive set piece report."""
    corner_routine: CornerRoutine
    free_kick_close: FreeKickSetup
    free_kick_medium: FreeKickSetup
    penalty_analysis: PenaltyAnalysis
    overall_set_piece_rating: str
