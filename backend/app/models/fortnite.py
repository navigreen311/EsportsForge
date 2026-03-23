"""Fortnite title-specific models — build sequences, edit drills, zone rotations."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class FNBuildType(str, enum.Enum):
    """Build sequence type classification."""

    RAMP_WALL = "ramp_wall"
    NINETIES = "90s"
    WATERFALL = "waterfall"
    HIGH_GROUND_RETAKE = "high_ground_retake"
    DOUBLE_RAMP = "double_ramp"
    SIDE_JUMP = "side_jump"
    THWIFO_CONE = "thwifo_cone"
    PROTECTED_RAMP_RUSH = "protected_ramp_rush"


class FNMasteryTier(str, enum.Enum):
    """Fortnite skill mastery tiers."""

    BEGINNER = "beginner"
    DEVELOPING = "developing"
    COMPETENT = "competent"
    ADVANCED = "advanced"
    ELITE = "elite"
    PRO = "pro"


class FNAntiCheatStatus(str, enum.Enum):
    """Anti-cheat verification result."""

    CLEAN = "clean"
    TIMING_ANOMALY = "timing_anomaly"
    INPUT_ANOMALY = "input_anomaly"
    MACRO_DETECTED = "macro_detected"
    INHUMAN_CONSISTENCY = "inhuman_consistency"
    REVIEW_REQUIRED = "review_required"


class FNBuildSession(UUIDPrimaryKeyMixin, Base):
    """
    Fortnite build training session — stores sequence analysis results.

    Tracks execution times, placement accuracy, material usage, and
    anti-cheat verification per build sequence attempt.
    """

    __tablename__ = "fn_build_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    build_type: Mapped[FNBuildType] = mapped_column(
        Enum(FNBuildType, name="fn_build_type", native_enum=True),
        nullable=False,
        index=True,
    )
    total_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    target_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    efficiency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    placement_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mastery_tier: Mapped[FNMasteryTier] = mapped_column(
        Enum(FNMasteryTier, name="fn_mastery_tier", native_enum=True),
        default=FNMasteryTier.BEGINNER,
        nullable=False,
        index=True,
    )
    anti_cheat_status: Mapped[FNAntiCheatStatus] = mapped_column(
        Enum(FNAntiCheatStatus, name="fn_anti_cheat_status", native_enum=True),
        default=FNAntiCheatStatus.CLEAN,
        nullable=False,
    )
    step_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Per-step timing and accuracy data"
    )
    material_used: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Materials consumed {wood, brick, metal}"
    )

    def __repr__(self) -> str:
        return f"<FNBuildSession {self.build_type.value} — {self.mastery_tier.value}>"


class FNEditDrill(UUIDPrimaryKeyMixin, Base):
    """
    Fortnite edit drill session — stores per-shape speed and accuracy.

    Tracks edit times, pressure performance, and dynamic calibration state.
    """

    __tablename__ = "fn_edit_drills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    avg_speed_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pressure_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mastery_tier: Mapped[FNMasteryTier] = mapped_column(
        Enum(FNMasteryTier, name="fn_mastery_tier", native_enum=True, create_type=False),
        default=FNMasteryTier.BEGINNER,
        nullable=False,
    )
    anti_cheat_status: Mapped[FNAntiCheatStatus] = mapped_column(
        Enum(FNAntiCheatStatus, name="fn_anti_cheat_status", native_enum=True, create_type=False),
        default=FNAntiCheatStatus.CLEAN,
        nullable=False,
    )
    shape_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Per-shape speed and accuracy breakdown"
    )
    calibration_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Dynamic calibration parameters"
    )

    def __repr__(self) -> str:
        return f"<FNEditDrill avg={self.avg_speed_ms}ms acc={self.accuracy}>"


class FNZoneRotation(UUIDPrimaryKeyMixin, Base):
    """
    Fortnite zone rotation record — stores rotation plan and outcome.

    Tracks zone tax, rotation style, path, and result.
    """

    __tablename__ = "fn_zone_rotations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    zone_phase: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rotation_style: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_tax_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    plan_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Full rotation plan with waypoints"
    )

    def __repr__(self) -> str:
        return f"<FNZoneRotation {self.zone_phase} — {self.rotation_style}>"


class FNPlayerTwin(UUIDPrimaryKeyMixin, Base):
    """
    Fortnite player digital twin — aggregated profile snapshot.

    Stores the latest twin profile with build/edit/zone/material analysis.
    """

    __tablename__ = "fn_player_twins"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    overall_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    build_style: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Build style profile"
    )
    edit_confidence: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Edit confidence profile"
    )
    zone_discipline: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Zone discipline profile"
    )
    material_management: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Material management profile"
    )
    anti_cheat_status: Mapped[FNAntiCheatStatus] = mapped_column(
        Enum(FNAntiCheatStatus, name="fn_anti_cheat_status", native_enum=True, create_type=False),
        default=FNAntiCheatStatus.CLEAN,
        nullable=False,
    )
    strengths: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )
    weaknesses: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )

    def __repr__(self) -> str:
        return f"<FNPlayerTwin rating={self.overall_rating}>"
