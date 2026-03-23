"""PGA TOUR 2K25 specific models — courses, rounds, shots, and golf intelligence."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class SwingSystemType(str, enum.Enum):
    """PGA 2K25 swing mechanic systems."""

    EVOSWING = "evoswing"
    SWING_STICK = "swing_stick"
    THREE_CLICK = "three_click"


class RoundType(str, enum.Enum):
    """Type of round played."""

    RANKED = "ranked"
    CASUAL = "casual"
    SOCIETY = "society"
    PRACTICE = "practice"
    TOURNAMENT = "tournament"


class PGA2K25Course(UUIDPrimaryKeyMixin, Base):
    """
    PGA TOUR 2K25 course — a golf course with hole-by-hole data.

    Stores course metadata and per-hole strategy information for CourseIQ.
    """

    __tablename__ = "pga2k25_courses"

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, unique=True
    )
    par: Mapped[int] = mapped_column(
        Integer, nullable=False, default=72
    )
    total_yardage: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    hole_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Per-hole par, yardage, hazards"
    )
    condition_presets: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Available condition presets"
    )

    # Relationships
    rounds: Mapped[list["PGA2K25Round"]] = relationship(
        back_populates="course", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PGA2K25Course {self.name} (par {self.par})>"


class PGA2K25Round(UUIDPrimaryKeyMixin, Base):
    """
    PGA TOUR 2K25 round — a single round of golf with scoring data.

    Tracks per-hole scores, shots, and conditions for session analysis.
    """

    __tablename__ = "pga2k25_rounds"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pga2k25_courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_type: Mapped[RoundType] = mapped_column(
        Enum(RoundType, name="pga2k25_round_type", native_enum=True), nullable=False
    )
    total_score: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    score_vs_par: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Score relative to par (e.g., -3)"
    )
    hole_scores: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Per-hole scoring breakdown"
    )
    putts_total: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    fairways_hit: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    greens_in_reg: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    conditions: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Wind, green speed, course condition"
    )

    # Relationships
    course: Mapped["PGA2K25Course"] = relationship(back_populates="rounds")
    shots: Mapped[list["PGA2K25Shot"]] = relationship(
        back_populates="round", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PGA2K25Round {self.total_score} ({self.score_vs_par:+d})>"


class PGA2K25Shot(UUIDPrimaryKeyMixin, Base):
    """
    PGA TOUR 2K25 shot — individual shot data for dispersion analysis.

    Captures club, distance, miss direction, lie, and pressure context
    to build accurate dispersion maps.
    """

    __tablename__ = "pga2k25_shots"

    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pga2k25_rounds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hole_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    shot_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    club: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    intended_distance: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    actual_distance: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    offline_yards: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Lateral miss: negative=left, positive=right"
    )
    long_short_yards: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0,
        comment="Distance miss: negative=short, positive=long"
    )
    lie: Mapped[str] = mapped_column(
        String(50), nullable=False, default="fairway"
    )
    wind_speed: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    pressure_situation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Relationships
    round: Mapped["PGA2K25Round"] = relationship(back_populates="shots")

    def __repr__(self) -> str:
        return f"<PGA2K25Shot hole={self.hole_number} #{self.shot_number} {self.club}>"


class PGA2K25SwingProfile(UUIDPrimaryKeyMixin, Base):
    """
    PGA TOUR 2K25 swing profile — per-user swing system and fault data.

    Stores the player's swing system choice and diagnosed faults for
    SwingForge analysis continuity.
    """

    __tablename__ = "pga2k25_swing_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    swing_system: Mapped[SwingSystemType] = mapped_column(
        Enum(SwingSystemType, name="pga2k25_swing_system", native_enum=True),
        nullable=False,
        default=SwingSystemType.EVOSWING,
    )
    faults: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Diagnosed swing faults"
    )
    club_profiles: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Per-club miss profiles"
    )
    overall_consistency: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )
    tempo_rating: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )

    def __repr__(self) -> str:
        return f"<PGA2K25SwingProfile {self.swing_system.value} consistency={self.overall_consistency:.0%}>"
