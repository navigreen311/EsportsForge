"""Pydantic schemas for Undisputed boxing AI agents."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class BoxingArchetype(str, enum.Enum):
    SWARMER = "swarmer"
    OUT_BOXER = "out_boxer"
    SLUGGER = "slugger"
    COUNTER_PUNCHER = "counter_puncher"
    BOXER_PUNCHER = "boxer_puncher"
    SWITCH_HITTER = "switch_hitter"


class StanceType(str, enum.Enum):
    ORTHODOX = "orthodox"
    SOUTHPAW = "southpaw"


class RingZone(str, enum.Enum):
    CENTER = "center"
    MID_RING = "mid_ring"
    ROPES = "ropes"
    CORNER = "corner"


class PunchType(str, enum.Enum):
    JAB = "jab"
    CROSS = "cross"
    LEAD_HOOK = "lead_hook"
    REAR_HOOK = "rear_hook"
    LEAD_UPPERCUT = "lead_uppercut"
    REAR_UPPERCUT = "rear_uppercut"
    BODY_JAB = "body_jab"
    BODY_HOOK = "body_hook"
    BODY_UPPERCUT = "body_uppercut"
    OVERHAND = "overhand"


class ComboRating(str, enum.Enum):
    ELITE = "elite"
    STRONG = "strong"
    AVERAGE = "average"
    POOR = "poor"


# ---------------------------------------------------------------------------
# BoxingIQ schemas
# ---------------------------------------------------------------------------

class ArchetypeClassification(BaseModel):
    primary_archetype: BoxingArchetype
    secondary_archetype: BoxingArchetype | None = None
    confidence: float = Field(..., ge=0, le=1.0)
    archetype_scores: dict[BoxingArchetype, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    description: str


class StanceAdvantage(BaseModel):
    advantage: float = Field(..., description="Positive = player advantage")
    lead_hand: str
    power_hand: str
    notes: str


class StanceMatchup(BaseModel):
    player_stance: StanceType
    opponent_stance: StanceType
    advantage: StanceAdvantage
    tips: list[str] = Field(default_factory=list)


class FightGameplan(BaseModel):
    player_archetype: BoxingArchetype
    opponent_archetype: BoxingArchetype
    matchup_edge: float
    win_probability: float = Field(..., ge=0, le=1.0)
    early_rounds: str
    mid_rounds: str
    late_rounds: str
    exploit_targets: list[str] = Field(default_factory=list)
    avoid_areas: list[str] = Field(default_factory=list)
    key_weapon: str
    fight_rounds: int


# ---------------------------------------------------------------------------
# FootworkForge schemas
# ---------------------------------------------------------------------------

class RingPosition(BaseModel):
    x: float = Field(..., ge=0, le=1.0)
    y: float = Field(..., ge=0, le=1.0)
    zone: RingZone


class RingPositionAnalysis(BaseModel):
    player_position: RingPosition
    opponent_position: RingPosition
    distance: float
    control_score: float = Field(..., ge=0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)


class RopeTracker(BaseModel):
    is_trapped: bool
    trap_severity: float = Field(..., ge=0, le=1.0)
    player_zone: RingZone
    nearest_corner_distance: float
    escape_routes: list[str] = Field(default_factory=list)


class CutOffAngle(BaseModel):
    angle_degrees: float
    move_x: float
    move_y: float
    opponent_likely_direction: str
    recommendation: str
    intercept_position: RingPosition


# ---------------------------------------------------------------------------
# ComboEV schemas
# ---------------------------------------------------------------------------

class PunchData(BaseModel):
    punch_type: PunchType
    base_damage: float
    adjusted_damage: float
    stamina_cost: float
    accuracy: float


class ComboAnalysis(BaseModel):
    punches: list[PunchData] = Field(default_factory=list)
    total_damage: float
    total_stamina: float
    ev: float = Field(..., description="Expected value: damage / stamina")
    rating: ComboRating
    opponent_guard: str | None = None
    distance: str | None = None
    notes: list[str] = Field(default_factory=list)


class GuardBreakReport(BaseModel):
    opponent_guard: str
    breaking_combos: list[dict[str, Any]] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


class JabEconomyReport(BaseModel):
    jabs_thrown: int
    jabs_landed: int
    jab_pct: float
    jab_accuracy: float
    jabs_per_round: float
    stamina_spent: float
    total_jab_damage: float
    jab_ev: float
    grade: str
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# JudgeMind schemas
# ---------------------------------------------------------------------------

class RoundScore(BaseModel):
    round_num: int
    player_score: int = Field(..., ge=7, le=10)
    opponent_score: int = Field(..., ge=7, le=10)
    winning: str = Field(..., description="player, opponent, or even")
    player_points: float
    opponent_points: float
    key_moment: str = ""


class ScorecardProjection(BaseModel):
    rounds_completed: int
    total_rounds: int
    player_total: int
    opponent_total: int
    margin: int
    player_rounds_won: int
    opponent_rounds_won: int
    even_rounds: int
    projected_winner: str
    projected_margin: float
    strategy: list[str] = Field(default_factory=list)


class RoundBankStrategy(BaseModel):
    current_margin: int
    rounds_remaining: int
    should_bank: bool
    should_push: bool
    stamina_pct: float
    reasoning: list[str] = Field(default_factory=list)


class BodyWorkROI(BaseModel):
    body_punches_landed: int
    body_per_round: float
    accumulated_effect: float
    stamina_drain_pct: float
    projected_total_body: float
    payoff_round: int
    roi_assessment: str
    current_round: int
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# DamageNarrative schemas
# ---------------------------------------------------------------------------

class DamageState(BaseModel):
    fight_id: str
    round_num: int
    round_damage: float
    cumulative_damage: float
    state: str = Field(..., description="fresh, worn, hurt, danger, desperate")
    recovery: float
    advice: list[str] = Field(default_factory=list)


class DamageTimeline(BaseModel):
    fight_id: str
    rounds: list[dict[str, Any]] = Field(default_factory=list)
    current_state: str
    cumulative_damage: float
    peak_damage_round: int
    peak_round_damage: float
    narrative: str


class PunchEconomyReport(BaseModel):
    punches_thrown: int
    punches_landed: int
    accuracy: float
    damage_dealt: float
    stamina_spent: float
    economy: float
    damage_per_punch: float
    per_round_thrown: float
    per_round_landed: float
    grade: str
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CampBuilder schemas
# ---------------------------------------------------------------------------

class CareerBuildPath(BaseModel):
    target_archetype: BoxingArchetype
    current_level: int
    available_points: int
    allocations: dict[str, int] = Field(default_factory=dict)
    priority_1: list[str] = Field(default_factory=list)
    priority_2: list[str] = Field(default_factory=list)
    priority_3: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)


class PunchPackage(BaseModel):
    name: str
    archetype: BoxingArchetype
    lead_punches: list[str] = Field(default_factory=list)
    power_punches: list[str] = Field(default_factory=list)
    body_punches: list[str] = Field(default_factory=list)
    specialty: str
    description: str


class TrainingCampPlan(BaseModel):
    player_archetype: BoxingArchetype
    opponent_archetype: BoxingArchetype
    fight_rounds: int
    weeks: int
    drills: list[str] = Field(default_factory=list)
    sparring_focus: list[str] = Field(default_factory=list)
    conditioning_notes: list[str] = Field(default_factory=list)
    week_plan: dict[str, str] = Field(default_factory=dict)
