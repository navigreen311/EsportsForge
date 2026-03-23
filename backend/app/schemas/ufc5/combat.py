"""Pydantic schemas for UFC 5 combat intelligence — damage, stamina, grappling, scoring."""

from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BodyRegion(str, enum.Enum):
    """Target zones for damage accumulation."""

    HEAD = "head"
    BODY = "body"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"


class StrikeType(str, enum.Enum):
    """Strike classifications in UFC 5."""

    JAB = "jab"
    CROSS = "cross"
    HOOK = "hook"
    UPPERCUT = "uppercut"
    OVERHAND = "overhand"
    BODY_HOOK = "body_hook"
    BODY_STRAIGHT = "body_straight"
    LEG_KICK = "leg_kick"
    CALF_KICK = "calf_kick"
    BODY_KICK = "body_kick"
    HEAD_KICK = "head_kick"
    SPINNING_BACK_KICK = "spinning_back_kick"
    SPINNING_BACK_FIST = "spinning_back_fist"
    FRONT_KICK = "front_kick"
    KNEE = "knee"
    ELBOW = "elbow"
    SUPERMAN_PUNCH = "superman_punch"
    FLYING_KNEE = "flying_knee"


class CutSeverity(str, enum.Enum):
    """Cut severity levels — affects doctor stoppage risk."""

    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class StaminaPhase(str, enum.Enum):
    """Round-phase stamina management zones."""

    FRESH = "fresh"
    CRUISING = "cruising"
    CONSERVING = "conserving"
    DEPLETED = "depleted"
    GASSED = "gassed"


class ArchetypeStyle(str, enum.Enum):
    """Fighter archetype classifications."""

    PRESSURE = "pressure"
    COUNTER = "counter"
    VOLUME = "volume"
    WRESTLER = "wrestler"
    GRAPPLER = "grappler"
    KICKBOXER = "kickboxer"
    BRAWLER = "brawler"
    POINT_FIGHTER = "point_fighter"
    SWITCH_STANCE = "switch_stance"


class GrapplePositionType(str, enum.Enum):
    """All grappling positions in UFC 5."""

    STANDING = "standing"
    SINGLE_LEG = "single_leg"
    DOUBLE_LEG = "double_leg"
    CLINCH = "clinch"
    THAI_CLINCH = "thai_clinch"
    HALF_GUARD_TOP = "half_guard_top"
    HALF_GUARD_BOTTOM = "half_guard_bottom"
    FULL_GUARD_TOP = "full_guard_top"
    FULL_GUARD_BOTTOM = "full_guard_bottom"
    SIDE_CONTROL_TOP = "side_control_top"
    SIDE_CONTROL_BOTTOM = "side_control_bottom"
    MOUNT_TOP = "mount_top"
    MOUNT_BOTTOM = "mount_bottom"
    BACK_CONTROL = "back_control"
    BACK_CONTROL_BOTTOM = "back_control_bottom"
    RUBBER_GUARD = "rubber_guard"
    BUTTERFLY_GUARD = "butterfly_guard"
    CRUCIFIX = "crucifix"


class SubmissionType(str, enum.Enum):
    """Submission types available in UFC 5."""

    REAR_NAKED_CHOKE = "rear_naked_choke"
    GUILLOTINE = "guillotine"
    ARM_TRIANGLE = "arm_triangle"
    TRIANGLE = "triangle"
    ARMBAR = "armbar"
    KIMURA = "kimura"
    OMOPLATA = "omoplata"
    DARCE = "darce"
    ANACONDA = "anaconda"
    HEEL_HOOK = "heel_hook"
    KNEEBAR = "kneebar"
    NECK_CRANK = "neck_crank"
    TWISTER = "twister"
    GOGOPLATA = "gogoplata"


class JudgeCriteria(str, enum.Enum):
    """UFC judging criteria priority."""

    EFFECTIVE_STRIKING = "effective_striking"
    EFFECTIVE_GRAPPLING = "effective_grappling"
    AGGRESSION = "aggression"
    OCTAGON_CONTROL = "octagon_control"


# ---------------------------------------------------------------------------
# FightIQ schemas
# ---------------------------------------------------------------------------


class FighterArchetype(BaseModel):
    """Opponent archetype classification with tendencies."""

    style: ArchetypeStyle = Field(..., description="Primary fighting style")
    secondary_style: Optional[ArchetypeStyle] = Field(
        None, description="Secondary style tendency"
    )
    stance: str = Field("orthodox", description="Primary stance")
    aggression_rating: float = Field(
        ..., ge=0.0, le=1.0, description="Aggression tendency 0-1"
    )
    takedown_threat: float = Field(
        ..., ge=0.0, le=1.0, description="Takedown likelihood per exchange"
    )
    clinch_tendency: float = Field(
        ..., ge=0.0, le=1.0, description="Clinch initiation tendency"
    )
    finish_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Historical finish rate"
    )
    common_openers: list[StrikeType] = Field(
        default_factory=list, description="Most frequent opening strikes"
    )
    danger_strikes: list[StrikeType] = Field(
        default_factory=list, description="Highest damage output strikes"
    )


class StyleMatchup(BaseModel):
    """Matchup analysis between two fighter archetypes."""

    player_style: ArchetypeStyle
    opponent_style: ArchetypeStyle
    advantage: float = Field(
        ..., ge=-1.0, le=1.0,
        description="Matchup advantage -1 (big disadvantage) to +1 (big advantage)",
    )
    key_strategies: list[str] = Field(
        default_factory=list, description="Recommended strategies for the matchup"
    )
    avoid_patterns: list[str] = Field(
        default_factory=list, description="Patterns to avoid in this matchup"
    )
    finish_windows: list[str] = Field(
        default_factory=list, description="Best moments to pursue a finish"
    )


class FinishPattern(BaseModel):
    """Analysis of how an archetype typically finishes fights."""

    archetype: ArchetypeStyle
    primary_finish: str = Field(..., description="Most common finish method")
    setup_sequence: list[str] = Field(
        default_factory=list, description="Steps leading to the finish"
    )
    round_tendency: int = Field(
        ..., ge=1, le=5, description="Most common round for finish"
    )
    success_rate: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# DamageForge schemas
# ---------------------------------------------------------------------------


class DamageEntry(BaseModel):
    """Single damage event in a fight."""

    region: BodyRegion = Field(..., description="Body part that received damage")
    strike_type: StrikeType = Field(..., description="Type of strike landed")
    damage_value: float = Field(
        ..., ge=0.0, le=100.0, description="Damage dealt 0-100"
    )
    is_critical: bool = Field(False, description="Whether the strike was a critical hit")
    round_number: int = Field(..., ge=1, le=5)
    timestamp_seconds: float = Field(
        ..., ge=0.0, description="Time in round when damage occurred"
    )


class DamageState(BaseModel):
    """Cumulative damage state across all body regions."""

    head_damage: float = Field(0.0, ge=0.0, le=100.0)
    body_damage: float = Field(0.0, ge=0.0, le=100.0)
    left_leg_damage: float = Field(0.0, ge=0.0, le=100.0)
    right_leg_damage: float = Field(0.0, ge=0.0, le=100.0)
    cut_severity: CutSeverity = Field(CutSeverity.NONE)
    cut_location: Optional[BodyRegion] = Field(None)
    stamina_drain_factor: float = Field(
        1.0, ge=0.5, le=3.0,
        description="Multiplier on stamina drain from accumulated damage",
    )
    knockout_vulnerability: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Probability modifier for KO from next clean head shot",
    )
    is_rocked: bool = Field(False, description="Currently in rocked state")
    damage_log: list[DamageEntry] = Field(default_factory=list)


class VulnerabilityWindow(BaseModel):
    """Time window where opponent is most vulnerable to damage."""

    trigger: str = Field(
        ..., description="What creates the window (e.g. whiffed overhand)"
    )
    duration_frames: int = Field(
        ..., ge=1, description="Duration of vulnerability in frames"
    )
    optimal_punish: list[StrikeType] = Field(
        default_factory=list, description="Best strikes to throw during window"
    )
    expected_damage: float = Field(
        ..., ge=0.0, le=100.0, description="Expected damage if punish lands"
    )
    body_target: BodyRegion = Field(
        ..., description="Best region to target during this window"
    )


# ---------------------------------------------------------------------------
# StaminaChain schemas
# ---------------------------------------------------------------------------


class StaminaEconomy(BaseModel):
    """Round-by-round stamina state and recommendations."""

    round_number: int = Field(..., ge=1, le=5)
    current_stamina: float = Field(
        ..., ge=0.0, le=100.0, description="Current stamina percentage"
    )
    phase: StaminaPhase = Field(..., description="Current stamina management phase")
    output_budget: int = Field(
        ..., ge=0, description="Recommended significant strikes remaining this round"
    )
    recovery_rate: float = Field(
        ..., ge=0.0, le=10.0, description="Stamina recovery per second at rest"
    )
    drain_rate: float = Field(
        ..., ge=0.0, le=20.0,
        description="Stamina drain per significant strike thrown",
    )
    whiff_penalty: float = Field(
        ..., ge=0.0, le=10.0,
        description="Extra stamina cost for missed strikes",
    )
    recommended_pace: str = Field(
        ..., description="Pace recommendation: explosive / measured / conserve"
    )
    opponent_stamina_estimate: float = Field(
        ..., ge=0.0, le=100.0,
        description="Estimated opponent stamina level",
    )


class WhiffPunishment(BaseModel):
    """Model for punishing opponent's missed strikes."""

    whiff_type: StrikeType = Field(..., description="Strike type that was whiffed")
    recovery_frames: int = Field(
        ..., ge=1, description="Frames opponent is in recovery"
    )
    optimal_counter: list[StrikeType] = Field(
        default_factory=list, description="Best counter strikes"
    )
    stamina_cost_to_opponent: float = Field(
        ..., ge=0.0, description="Stamina the whiff cost the opponent"
    )


# ---------------------------------------------------------------------------
# GrappleGraph schemas
# ---------------------------------------------------------------------------


class GrappleTransition(BaseModel):
    """A single transition option from a grapple position."""

    from_position: GrapplePositionType
    to_position: GrapplePositionType
    input_sequence: str = Field(
        ..., description="Controller input for this transition"
    )
    stamina_cost: float = Field(..., ge=0.0, le=30.0)
    success_rate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Base success rate before attribute modifiers",
    )
    denial_window_frames: int = Field(
        ..., ge=1, description="Frames where opponent can deny"
    )
    leads_to_submission: bool = Field(
        False, description="Whether this transition opens a submission"
    )


class GrapplePosition(BaseModel):
    """Full decision tree for a grapple position."""

    position: GrapplePositionType
    is_dominant: bool = Field(
        ..., description="Whether this is a dominant position"
    )
    available_transitions: list[GrappleTransition] = Field(default_factory=list)
    available_strikes: list[StrikeType] = Field(
        default_factory=list, description="Ground strikes available"
    )
    available_submissions: list[SubmissionType] = Field(
        default_factory=list, description="Submissions available from this position"
    )
    escape_options: list[GrappleTransition] = Field(
        default_factory=list, description="Escapes if in bottom position"
    )
    priority_action: str = Field(
        ..., description="Recommended primary action from this position"
    )
    stamina_drain_per_second: float = Field(
        ..., ge=0.0, le=5.0,
        description="Passive stamina drain while in this position",
    )


class SubmissionChain(BaseModel):
    """Multi-step submission sequence awareness."""

    entry_position: GrapplePositionType
    submission: SubmissionType
    setup_transitions: list[GrappleTransition] = Field(
        default_factory=list,
        description="Transition chain to reach submission position",
    )
    gate_count: int = Field(
        ..., ge=1, le=5, description="Number of submission gates to pass"
    )
    stamina_threshold: float = Field(
        ..., ge=0.0, le=100.0,
        description="Opponent stamina below which submission chance spikes",
    )
    chain_alternatives: list[SubmissionType] = Field(
        default_factory=list,
        description="Alternative subs if opponent defends primary",
    )


# ---------------------------------------------------------------------------
# RoundScore schemas
# ---------------------------------------------------------------------------


class RoundScore(BaseModel):
    """Judge-aware scoring model for a single round."""

    round_number: int = Field(..., ge=1, le=5)
    player_score: int = Field(
        ..., ge=7, le=10, description="Player's round score (10-point must)"
    )
    opponent_score: int = Field(
        ..., ge=7, le=10, description="Opponent's round score (10-point must)"
    )
    significant_strikes_landed: int = Field(0, ge=0)
    significant_strikes_absorbed: int = Field(0, ge=0)
    takedowns_landed: int = Field(0, ge=0)
    takedowns_defended: int = Field(0, ge=0)
    control_time_seconds: float = Field(0.0, ge=0.0)
    knockdowns_scored: int = Field(0, ge=0)
    knockdowns_received: int = Field(0, ge=0)
    dominant_criteria: list[JudgeCriteria] = Field(
        default_factory=list,
        description="Criteria player is winning this round",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence that player won this round",
    )
    swing_round: bool = Field(
        False, description="Whether this round is too close to call"
    )


class RoundPlan(BaseModel):
    """Pre-round tactical script."""

    round_number: int = Field(..., ge=1, le=5)
    opening_sequence: list[str] = Field(
        default_factory=list,
        description="First 30 seconds scripted actions",
    )
    target_region: BodyRegion = Field(
        ..., description="Primary damage target for this round"
    )
    pace: str = Field(
        ..., description="Round pace: blitz / steady / coast / survive"
    )
    finish_attempt: bool = Field(
        False, description="Whether to pursue a finish this round"
    )
    scorecard_status: str = Field(
        ..., description="Current perceived scorecard state"
    )
    adjustments: list[str] = Field(
        default_factory=list,
        description="Tactical adjustments from previous rounds",
    )


class FinishProtocol(BaseModel):
    """Protocol for pursuing a finish when conditions are met."""

    trigger_conditions: list[str] = Field(
        ..., description="Conditions that activate finish pursuit"
    )
    method: str = Field(..., description="TKO / KO / SUB")
    strike_sequence: list[StrikeType] = Field(
        default_factory=list,
        description="Strike sequence for TKO/KO finish",
    )
    submission_chain: Optional[SubmissionChain] = Field(
        None, description="Submission chain for SUB finish"
    )
    stamina_required: float = Field(
        ..., ge=0.0, le=100.0,
        description="Minimum stamina to attempt finish",
    )
    abort_conditions: list[str] = Field(
        default_factory=list,
        description="When to abandon the finish attempt",
    )


# ---------------------------------------------------------------------------
# OnlineCareer schemas
# ---------------------------------------------------------------------------


class PerkRanking(BaseModel):
    """Ranking of a perk for a given fighter build."""

    perk_name: str
    tier: str = Field(..., description="S / A / B / C / D tier")
    synergy_styles: list[ArchetypeStyle] = Field(
        default_factory=list,
        description="Styles that benefit most from this perk",
    )
    win_rate_impact: float = Field(
        ..., ge=-0.1, le=0.1,
        description="Estimated win rate delta when equipped",
    )
    description: str = Field("", description="What the perk does")


class FighterStylePath(BaseModel):
    """Style progression path with win rate data."""

    style: ArchetypeStyle
    weight_class: str
    win_rate: float = Field(..., ge=0.0, le=1.0)
    recommended_perks: list[PerkRanking] = Field(default_factory=list)
    key_attributes: dict[str, int] = Field(
        default_factory=dict,
        description="Attribute name -> recommended minimum value",
    )
    skill_priority: list[str] = Field(
        default_factory=list,
        description="Skills to level up in priority order",
    )


class FighterBuild(BaseModel):
    """Complete fighter build specification for online career."""

    name: str = Field(..., description="Build name")
    weight_class: str = Field(..., description="Weight class")
    style_path: FighterStylePath
    archetype: FighterArchetype
    equipped_perks: list[PerkRanking] = Field(
        default_factory=list, max_length=5,
    )
    attributes: dict[str, int] = Field(
        default_factory=dict,
        description="Attribute allocations",
    )
    overall_rating: float = Field(
        ..., ge=0.0, le=100.0, description="Build overall rating"
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    matchup_notes: dict[str, str] = Field(
        default_factory=dict,
        description="Style -> how to fight them with this build",
    )
