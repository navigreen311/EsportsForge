"""Fortnite gameplay schemas — building, editing, zone play, meta, and twin."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class BuildType(str, Enum):
    """Core build sequence archetypes."""

    RAMP_WALL = "ramp_wall"
    NINETIES = "90s"
    WATERFALL = "waterfall"
    HIGH_GROUND_RETAKE = "high_ground_retake"
    DOUBLE_RAMP = "double_ramp"
    SIDE_JUMP = "side_jump"
    THWIFO_CONE = "thwifo_cone"
    PROTECTED_RAMP_RUSH = "protected_ramp_rush"


class EditShape(str, Enum):
    """Edit tile shape classifications."""

    TRIANGLE = "triangle"
    ARCH = "arch"
    DOOR = "door"
    WINDOW = "window"
    HALF_WALL = "half_wall"
    CORNER = "corner"
    PEANUT = "peanut"
    STAIRS_EDIT = "stairs_edit"


class MaterialType(str, Enum):
    """Fortnite material types."""

    WOOD = "wood"
    BRICK = "brick"
    METAL = "metal"


class ZonePhase(str, Enum):
    """Storm zone phases."""

    EARLY_GAME = "early_game"
    FIRST_ZONE = "first_zone"
    SECOND_ZONE = "second_zone"
    THIRD_ZONE = "third_zone"
    FOURTH_ZONE = "fourth_zone"
    MOVING_ZONE = "moving_zone"
    HALF_HALF = "half_half"
    ENDGAME = "endgame"


class RotationStyle(str, Enum):
    """Rotation strategy archetypes."""

    EARLY_ROTATE = "early_rotate"
    EDGE_ROTATE = "edge_rotate"
    TARPING = "tarping"
    TUNNELING = "tunneling"
    LAUNCH_PAD = "launch_pad"
    VEHICLE_ROTATE = "vehicle_rotate"
    STORM_SURGE_PLAY = "storm_surge_play"


class AugmentRarity(str, Enum):
    """Augment rarity tiers."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class MasteryTier(str, Enum):
    """Skill mastery tiers for build/edit."""

    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    ADVANCED = "advanced"
    ELITE = "elite"
    PRO = "pro"


class AntiCheatFlag(str, Enum):
    """Anti-cheat verification flags."""

    CLEAN = "clean"
    TIMING_ANOMALY = "timing_anomaly"
    INPUT_ANOMALY = "input_anomaly"
    MACRO_DETECTED = "macro_detected"
    INHUMAN_CONSISTENCY = "inhuman_consistency"
    REVIEW_REQUIRED = "review_required"


# ---------------------------------------------------------------------------
# BuildForge FN schemas
# ---------------------------------------------------------------------------

class BuildSequenceStep(BaseModel):
    """A single step within a build sequence."""

    step_number: int = Field(..., ge=1, description="Step order in the sequence.")
    action: str = Field(..., description="Build action (e.g., 'place wall', 'place ramp').")
    key_bind: str | None = Field(None, description="Expected key/button press.")
    target_time_ms: int = Field(..., ge=0, description="Target execution time in ms.")
    actual_time_ms: int | None = Field(None, ge=0, description="Actual time achieved.")
    notes: str | None = None


class BuildSequenceAnalysis(BaseModel):
    """Full analysis of a build sequence attempt."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    build_type: BuildType
    steps: list[BuildSequenceStep]
    total_time_ms: int = Field(..., ge=0)
    target_time_ms: int = Field(..., ge=0)
    efficiency_score: float = Field(..., ge=0.0, le=1.0)
    placement_accuracy: float = Field(..., ge=0.0, le=1.0)
    material_used: dict[MaterialType, int] = Field(default_factory=dict)
    mastery_tier: MasteryTier = MasteryTier.BEGINNER
    anti_cheat: AntiCheatFlag = AntiCheatFlag.CLEAN
    improvement_tips: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BuildDrillPrescription(BaseModel):
    """Prescribed building drill based on weaknesses."""

    build_type: BuildType
    focus_area: str = Field(..., description="Specific weakness to address.")
    reps_prescribed: int = Field(default=10, ge=1)
    target_time_ms: int = Field(..., ge=0)
    difficulty_level: int = Field(default=1, ge=1, le=5)
    warm_up_sequence: list[str] = Field(default_factory=list)


class BuildForgeReport(BaseModel):
    """BuildForge session report with drill prescriptions."""

    user_id: str
    session_id: UUID = Field(default_factory=uuid4)
    sequences_analyzed: list[BuildSequenceAnalysis]
    overall_mastery: MasteryTier
    weakest_sequence: BuildType
    strongest_sequence: BuildType
    drills: list[BuildDrillPrescription]
    material_efficiency: float = Field(..., ge=0.0, le=1.0)
    anti_cheat_status: AntiCheatFlag = AntiCheatFlag.CLEAN
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# EditForge schemas
# ---------------------------------------------------------------------------

class EditAttempt(BaseModel):
    """A single edit attempt with timing."""

    shape: EditShape
    time_ms: int = Field(..., ge=0, description="Time to complete edit in ms.")
    successful: bool = True
    under_pressure: bool = False
    reset_clean: bool = Field(True, description="Whether edit was reset cleanly.")


class EditSpeedProfile(BaseModel):
    """Player's edit speed profile across all shapes."""

    user_id: str
    shape_speeds: dict[EditShape, float] = Field(
        default_factory=dict,
        description="Average speed per shape in ms.",
    )
    shape_accuracy: dict[EditShape, float] = Field(
        default_factory=dict,
        description="Accuracy rate per shape (0-1).",
    )
    pressure_penalty: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Performance drop-off under pressure (0=no drop, 1=total fail).",
    )
    mastery_tier: MasteryTier = MasteryTier.BEGINNER
    anti_cheat: AntiCheatFlag = AntiCheatFlag.CLEAN
    calibration_version: int = Field(default=1, ge=1)


class EditDrillResult(BaseModel):
    """Result of an edit training drill."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    attempts: list[EditAttempt]
    avg_speed_ms: float = Field(..., ge=0.0)
    accuracy: float = Field(..., ge=0.0, le=1.0)
    pressure_accuracy: float = Field(..., ge=0.0, le=1.0)
    shapes_drilled: list[EditShape]
    mastery_tier: MasteryTier = MasteryTier.BEGINNER
    anti_cheat: AntiCheatFlag = AntiCheatFlag.CLEAN
    dynamic_calibration: dict[str, float] = Field(
        default_factory=dict,
        description="Dynamic calibration adjustments applied.",
    )
    improvement_notes: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# ZoneForge FN schemas
# ---------------------------------------------------------------------------

class StormState(BaseModel):
    """Current storm / zone state."""

    zone_phase: ZonePhase
    seconds_until_close: int = Field(..., ge=0)
    storm_damage_per_tick: float = Field(..., ge=0.0)
    safe_zone_center: tuple[float, float] = Field(
        ..., description="(x, y) of safe zone center."
    )
    safe_zone_radius: float = Field(..., ge=0.0)
    next_zone_center: tuple[float, float] | None = None
    next_zone_radius: float | None = None


class PlayerPosition(BaseModel):
    """Player position and state for zone analysis."""

    x: float
    y: float
    health: int = Field(..., ge=0, le=100)
    shield: int = Field(..., ge=0, le=100)
    materials: dict[MaterialType, int] = Field(default_factory=dict)
    has_mobility_item: bool = False
    elimination_count: int = Field(default=0, ge=0)
    alive_players: int = Field(default=100, ge=1)


class ZoneTax(BaseModel):
    """Zone tax calculation — cost of being out of position."""

    material_cost: int = Field(default=0, ge=0, description="Mats needed for rotation.")
    health_risk: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of taking storm damage."
    )
    fight_probability: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability of third-party encounter."
    )
    time_pressure: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Time pressure index."
    )
    total_tax_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Composite zone tax."
    )


class RotationPlan(BaseModel):
    """Optimal rotation plan for current zone state."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    storm_state: StormState
    player_position: PlayerPosition
    recommended_style: RotationStyle
    zone_tax: ZoneTax
    path_waypoints: list[tuple[float, float]] = Field(default_factory=list)
    third_party_risk_zones: list[tuple[float, float]] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# FortniteMeta AI schemas
# ---------------------------------------------------------------------------

class WeaponMeta(BaseModel):
    """Weapon meta analysis entry."""

    weapon_name: str
    weapon_class: str = Field(..., description="AR, SMG, Shotgun, Sniper, etc.")
    tier: str = Field(..., description="Current tier: S/A/B/C/D.")
    dps: float = Field(..., ge=0.0)
    pick_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    win_rate_correlation: float = Field(default=0.0, ge=-1.0, le=1.0)
    best_range: str = Field(default="medium")
    notes: str | None = None


class AugmentPriority(BaseModel):
    """Augment priority ranking for current meta."""

    augment_name: str
    rarity: AugmentRarity
    priority_rank: int = Field(..., ge=1)
    synergy_score: float = Field(default=0.0, ge=0.0, le=1.0)
    playstyle_fit: str = Field(..., description="Aggressive, passive, balanced.")
    take_rate: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str = ""


class MobilityItem(BaseModel):
    """Mobility item optimization entry."""

    item_name: str
    availability: str = Field(..., description="floor_loot, chest, supply_drop, etc.")
    rotation_value: float = Field(..., ge=0.0, le=1.0)
    combat_value: float = Field(..., ge=0.0, le=1.0)
    carry_priority: int = Field(..., ge=1, le=5)
    best_use_phase: ZonePhase


class MetaSnapshot(BaseModel):
    """Full meta snapshot for current season/patch."""

    id: UUID = Field(default_factory=uuid4)
    patch_version: str
    season: str
    weapon_tier_list: list[WeaponMeta]
    augment_priorities: list[AugmentPriority]
    mobility_items: list[MobilityItem]
    loot_pool_notes: list[str] = Field(default_factory=list)
    meta_shift_summary: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# FortniteTwin schemas
# ---------------------------------------------------------------------------

class BuildStyleProfile(BaseModel):
    """Build style fingerprint."""

    primary_style: str = Field(..., description="Cranker, boxer, piece-controller, etc.")
    build_speed_tier: MasteryTier = MasteryTier.BEGINNER
    preferred_sequences: list[BuildType] = Field(default_factory=list)
    material_preference: MaterialType = MaterialType.WOOD
    overbuilding_index: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How much the player overbuilds (0=efficient, 1=excessive).",
    )


class EditConfidence(BaseModel):
    """Edit confidence profile."""

    fastest_shape: EditShape | None = None
    slowest_shape: EditShape | None = None
    avg_speed_ms: float = Field(default=0.0, ge=0.0)
    pressure_reliability: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Edit success rate under pressure.",
    )
    edit_to_shoot_speed_ms: float = Field(
        default=0.0, ge=0.0,
        description="Time from edit confirm to first shot.",
    )


class ZoneDiscipline(BaseModel):
    """Zone discipline and rotation analysis."""

    avg_rotation_timing: str = Field(
        default="on_time",
        description="early, on_time, late, storm_surfer.",
    )
    zone_death_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Rate of dying to storm.",
    )
    positioning_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Average positioning quality when zone closes.",
    )
    rotation_fight_win_rate: float = Field(
        default=0.0, ge=0.0, le=1.0,
    )


class MaterialManagement(BaseModel):
    """Material management patterns."""

    avg_mats_at_endgame: dict[MaterialType, int] = Field(default_factory=dict)
    farming_efficiency: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Materials gathered per minute relative to optimal.",
    )
    waste_index: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Percentage of placed builds that served no purpose.",
    )
    material_split_balance: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Balance across wood/brick/metal (1.0 = perfectly balanced).",
    )


class FortniteTwinProfile(BaseModel):
    """Complete Fortnite digital twin — player fingerprint."""

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    build_style: BuildStyleProfile
    edit_confidence: EditConfidence
    zone_discipline: ZoneDiscipline
    material_management: MaterialManagement
    overall_rating: float = Field(default=0.0, ge=0.0, le=100.0)
    anti_cheat_status: AntiCheatFlag = AntiCheatFlag.CLEAN
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_focus: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
