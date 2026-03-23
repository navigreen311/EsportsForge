"""Madden 26 specific models — schemes, plays, and football intelligence."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class SchemeType(str, enum.Enum):
    """Offensive or defensive scheme classification."""

    OFFENSE = "offense"
    DEFENSE = "defense"


class MaddenScheme(UUIDPrimaryKeyMixin, Base):
    """
    Madden 26 scheme — an offensive or defensive system.

    Contains concepts and coverage matrix data for AI analysis.
    """

    __tablename__ = "madden_schemes"

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    type: Mapped[SchemeType] = mapped_column(
        Enum(SchemeType, name="scheme_type", native_enum=True), nullable=False
    )
    concepts: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Core scheme concepts and principles"
    )
    coverage_matrix: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Coverage matchup matrix"
    )

    # Relationships
    plays: Mapped[list["MaddenPlay"]] = relationship(
        back_populates="scheme", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MaddenScheme {self.name} ({self.type.value})>"


class MaddenPlay(UUIDPrimaryKeyMixin, Base):
    """
    Madden 26 play — an individual play within a scheme.

    Tracks formation, success rate, and situational effectiveness.
    """

    __tablename__ = "madden_plays"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("madden_schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    formation: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    play_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g. pass, run, RPO, screen"
    )
    success_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    situation_tags: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Situational tags: down, distance, field_zone"
    )

    # Relationships
    scheme: Mapped["MaddenScheme"] = relationship(back_populates="plays")

    def __repr__(self) -> str:
        return f"<MaddenPlay {self.name} ({self.formation})>"
