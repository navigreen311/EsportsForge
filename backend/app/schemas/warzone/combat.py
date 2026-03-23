"""Pydantic schemas for Warzone combat analysis, loadouts, and zone intelligence."""

from __future__ import annotations

import enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WeaponClass(str, enum.Enum):
    """Warzone weapon categories."""

    ASSAULT_RIFLE = "assault_rifle"
    SMG = "smg"
    LMG = "lmg"
    SNIPER = "sniper"
    MARKSMAN = "marksman"
    SHOTGUN = "shotgun"
    PISTOL = "pistol"
    LAUNCHER = "launcher"
    MELEE = "melee"


class WeaponTier(str, enum.Enum):
    """Meta tier ranking for weapons."""

    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class EngagementRange(str, enum.Enum):
    """Combat engagement distance bands."""

    CQB = "cqb"              # 0-10m
    SHORT = "short"           # 10-25m
    MEDIUM = "medium"         # 25-50m
    LONG = "long"             # 50-100m
    EXTREME = "extreme"       # 100m+


class CirclePhase(str, enum.Enum):
    """Gas circle phases in a Warzone match."""

    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    PHASE_4 = "phase_4"
    PHASE_5 = "phase_5"
    FINAL = "final"


class SquadRole(str, enum.Enum):
    """Warzone squad role designations."""

    IGL = "igl"               # In-game leader
    FRAGGER = "fragger"       # Entry / aggro kills
    SUPPORT = "support"       # Utility / buybacks
    SNIPER = "sniper"         # Long-range picks
    FLEX = "flex"             # Adapts to need


class MovementStyle(str, enum.Enum):
    """Player movement tendency classification."""

    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"
    BALANCED = "balanced"
    ROTATION_HEAVY = "rotation_heavy"
    EDGE_PLAYER = "edge_player"


class EngagementTendency(str, enum.Enum):
    """How a player typically initiates fights."""

    FIRST_MOVER = "first_mover"
    REACTIVE = "reactive"
    OPPORTUNISTIC = "opportunistic"
    AVOIDANT = "avoidant"


# ---------------------------------------------------------------------------
# Zone / rotation schemas
# ---------------------------------------------------------------------------

class ZoneRequest(BaseModel):
    """Request for circle collapse prediction."""

    current_phase: CirclePhase = Field(..., description="Current circle phase")
    player_position: tuple[float, float] = Field(
        ..., description="Player grid coords (x, y)"
    )
    teammate_positions: list[tuple[float, float]] = Field(
        default_factory=list, description="Squad mate positions"
    )
    known_enemy_positions: list[tuple[float, float]] = Field(
        default_factory=list, description="Spotted enemy positions"
    )
    map_name: str = Field("urzikstan", description="Active map name")


class CirclePrediction(BaseModel):
    """Predicted next circle center and timing."""

    predicted_center: tuple[float, float] = Field(
        ..., description="Predicted center coordinates"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    safe_zone_radius: float = Field(..., description="Predicted safe radius in meters")
    collapse_eta_seconds: int = Field(..., description="Seconds until collapse")
    phase: CirclePhase


class ThirdPartyRisk(BaseModel):
    """Risk assessment of getting third-partied during rotation."""

    risk_score: float = Field(..., ge=0.0, le=1.0, description="0=safe, 1=certain ambush")
    threat_direction: str = Field(..., description="Cardinal direction of threat")
    enemy_count_estimate: int = Field(..., ge=0)
    mitigation: str = Field(..., description="Recommended counter-play")


class RotationPlan(BaseModel):
    """Complete rotation recommendation."""

    waypoints: list[tuple[float, float]] = Field(
        ..., description="Ordered waypoint coordinates"
    )
    estimated_travel_seconds: int
    cover_quality: float = Field(
        ..., ge=0.0, le=1.0, description="Cover availability along route"
    )
    third_party_risk: ThirdPartyRisk
    notes: str = Field("", description="Tactical notes")


class RotationRequest(BaseModel):
    """Request for rotation planning."""

    current_position: tuple[float, float]
    destination: tuple[float, float]
    phase: CirclePhase
    squad_size: int = Field(4, ge=1, le=4)
    has_vehicle: bool = False


class ZoneResponse(BaseModel):
    """Full zone intelligence response."""

    prediction: CirclePrediction
    rotation_plan: RotationPlan
    third_party_risks: list[ThirdPartyRisk]
    summary: str


# ---------------------------------------------------------------------------
# Loadout / weapon meta schemas
# ---------------------------------------------------------------------------

class AttachmentTradeOff(BaseModel):
    """Trade-off analysis for a single attachment slot."""

    slot: str = Field(..., description="e.g. 'muzzle', 'barrel', 'optic'")
    recommended: str = Field(..., description="Best attachment for this slot")
    alternative: Optional[str] = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    stat_changes: dict[str, float] = Field(
        default_factory=dict,
        description="Stat deltas, e.g. {'recoil_control': +8, 'ads_speed': -3}",
    )


class WeaponMeta(BaseModel):
    """Weekly meta analysis for a single weapon."""

    weapon_name: str
    weapon_class: WeaponClass
    tier: WeaponTier
    pick_rate: float = Field(..., ge=0.0, le=1.0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    ttk_ms: int = Field(..., description="Time to kill in milliseconds at optimal range")
    effective_range: EngagementRange
    best_attachments: list[AttachmentTradeOff] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    patch_trend: str = Field(
        "stable", description="'buffed', 'nerfed', or 'stable' since last patch"
    )


class LoadoutBuild(BaseModel):
    """A complete Warzone loadout recommendation."""

    primary: WeaponMeta
    secondary: WeaponMeta
    perks: list[str] = Field(default_factory=list)
    tactical: str = Field("stun_grenade")
    lethal: str = Field("semtex")
    playstyle_fit: str = Field(
        ..., description="Playstyle this loadout is optimized for"
    )
    effectiveness_score: float = Field(..., ge=0.0, le=100.0)


class LoadoutOptimizeRequest(BaseModel):
    """Request to optimize a loadout."""

    preferred_class: Optional[WeaponClass] = None
    playstyle: MovementStyle = MovementStyle.BALANCED
    engagement_range: EngagementRange = EngagementRange.MEDIUM
    map_name: str = "urzikstan"


class LoadoutOptimizeResponse(BaseModel):
    """Loadout optimization result."""

    recommended_loadout: LoadoutBuild
    alternatives: list[LoadoutBuild] = Field(default_factory=list)
    meta_tier_list: list[WeaponMeta] = Field(default_factory=list)
    summary: str


# ---------------------------------------------------------------------------
# Gunfight / combat schemas
# ---------------------------------------------------------------------------

class RecoilPattern(BaseModel):
    """Recoil pattern analysis for a weapon."""

    weapon_name: str
    weapon_class: WeaponClass
    vertical_pull: float = Field(..., description="Vertical recoil magnitude")
    horizontal_drift: float = Field(..., description="Horizontal deviation")
    pattern_shape: str = Field(
        ..., description="e.g. 'vertical_climb', 'S_curve', 'left_pull'"
    )
    compensation_instruction: str = Field(
        ..., description="How to counter the recoil"
    )
    difficulty_rating: float = Field(..., ge=0.0, le=10.0)
    first_5_bullets_accuracy: float = Field(
        ..., ge=0.0, le=1.0, description="Accuracy of first 5 rounds on target"
    )


class FirstBulletDrill(BaseModel):
    """Training drill for first bullet accuracy."""

    drill_name: str
    description: str
    target_accuracy: float = Field(..., ge=0.0, le=1.0)
    recommended_sensitivity: dict[str, float] = Field(
        default_factory=dict, description="Sens settings for drill"
    )
    warmup_reps: int = Field(10)
    focus_areas: list[str] = Field(default_factory=list)


class EngagementDecision(BaseModel):
    """Decision engine output for whether to take a fight."""

    should_engage: bool
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    optimal_range: EngagementRange
    recommended_approach: str = Field(
        ..., description="e.g. 'push', 'hold', 'disengage', 'reposition'"
    )
    ttk_advantage_ms: int = Field(
        0, description="Positive = you win the TTK race"
    )


class GunfightAnalysis(BaseModel):
    """Complete gunfight intelligence package."""

    recoil_patterns: list[RecoilPattern] = Field(default_factory=list)
    first_bullet_drills: list[FirstBulletDrill] = Field(default_factory=list)
    engagement_decision: Optional[EngagementDecision] = None
    summary: str


# ---------------------------------------------------------------------------
# Squad ops schemas
# ---------------------------------------------------------------------------

class SquadMember(BaseModel):
    """Individual squad member profile for role assignment."""

    player_id: str
    gamertag: str
    kd_ratio: float = Field(..., ge=0.0)
    avg_damage: float = Field(..., ge=0.0)
    win_rate: float = Field(..., ge=0.0, le=1.0)
    preferred_range: EngagementRange = EngagementRange.MEDIUM
    comms_score: float = Field(
        0.5, ge=0.0, le=1.0, description="Communication effectiveness"
    )
    clutch_rate: float = Field(0.0, ge=0.0, le=1.0)


class RoleAssignment(BaseModel):
    """Role assignment for a squad member."""

    player_id: str
    gamertag: str
    assigned_role: SquadRole
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    recommended_loadout_style: str


class RevivePriority(BaseModel):
    """Decision engine for who to revive first in a multi-down scenario."""

    priority_order: list[str] = Field(
        ..., description="Player IDs in revive priority order"
    )
    reasoning: list[str] = Field(
        ..., description="One reason per player in order"
    )
    context: str = Field(..., description="Situation context driving the decision")


class SquadOpsRequest(BaseModel):
    """Request for squad operations analysis."""

    squad: list[SquadMember]
    match_context: Optional[str] = None


class SquadAnalysis(BaseModel):
    """Full squad operations intelligence."""

    role_assignments: list[RoleAssignment]
    revive_priority: RevivePriority
    callout_efficiency: float = Field(
        ..., ge=0.0, le=1.0, description="Squad comms efficiency score"
    )
    squad_synergy_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall squad synergy rating"
    )
    improvement_tips: list[str] = Field(default_factory=list)
    summary: str


# ---------------------------------------------------------------------------
# WarzoneTwin schemas
# ---------------------------------------------------------------------------

class ClutchProfile(BaseModel):
    """Clutch performance metrics."""

    clutch_rate: float = Field(..., ge=0.0, le=1.0)
    avg_kills_in_clutch: float = Field(..., ge=0.0)
    composure_rating: float = Field(
        ..., ge=0.0, le=10.0, description="How calm under pressure"
    )
    best_clutch_range: EngagementRange


class LootEfficiency(BaseModel):
    """Loot pathing efficiency metrics."""

    avg_loot_time_seconds: float = Field(..., ge=0.0)
    loadout_acquisition_rate: float = Field(
        ..., ge=0.0, le=1.0, description="How often player gets loadout drop"
    )
    cash_per_minute: float = Field(..., ge=0.0)
    efficiency_grade: str = Field(..., description="A+ through F")


class WarzoneTwinRequest(BaseModel):
    """Request to build a player digital twin."""

    player_id: str
    gamertag: str
    recent_matches: int = Field(20, ge=1, le=100)
    match_history: list[dict[str, Any]] = Field(
        default_factory=list, description="Raw match data for analysis"
    )


class WarzoneTwinProfile(BaseModel):
    """Complete Warzone digital twin profile."""

    player_id: str
    gamertag: str
    movement_style: MovementStyle
    engagement_tendency: EngagementTendency
    clutch_profile: ClutchProfile
    loot_efficiency: LootEfficiency
    avg_placement: float = Field(..., ge=1.0)
    avg_kills: float = Field(..., ge=0.0)
    kd_ratio: float = Field(..., ge=0.0)
    preferred_weapons: list[str] = Field(default_factory=list)
    hot_drop_rate: float = Field(
        ..., ge=0.0, le=1.0, description="How often they drop contested POIs"
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    coaching_tips: list[str] = Field(default_factory=list)
    summary: str
