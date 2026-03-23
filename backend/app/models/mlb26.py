"""MLB The Show 26 specific models — pitchers, batters, and Diamond Dynasty cards."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class PitcherRole(str, enum.Enum):
    """Pitching staff role."""
    STARTER = "starter"
    CLOSER = "closer"
    SETUP = "setup"
    LONG_RELIEF = "long_relief"
    MIDDLE_RELIEF = "middle_relief"


class MLBPlayer(UUIDPrimaryKeyMixin, Base):
    """
    MLB The Show 26 player card — Diamond Dynasty card data.

    Stores ratings, attributes, and market metadata for a player card.
    """

    __tablename__ = "mlb_players"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    overall: Mapped[int] = mapped_column(Integer, nullable=False)
    tier: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="common, bronze, silver, gold, diamond"
    )
    bats: Mapped[str] = mapped_column(String(1), nullable=False, comment="L, R, or S")
    throws: Mapped[str] = mapped_column(String(1), nullable=False, comment="L or R")
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Full attribute breakdown: contact, power, speed, etc."
    )
    market_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    lineup_slots: Mapped[list["MLBLineupSlot"]] = relationship(
        back_populates="player", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLBPlayer {self.name} ({self.position} {self.overall})>"


class MLBLineup(UUIDPrimaryKeyMixin, Base):
    """
    MLB The Show 26 lineup — a saved Diamond Dynasty batting order.
    """

    __tablename__ = "mlb_lineups"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platoon: Mapped[str] = mapped_column(
        String(20), default="vs_rhp", nullable=False
    )
    overall_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    slots: Mapped[list["MLBLineupSlot"]] = relationship(
        back_populates="lineup", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MLBLineup {self.name} ({self.overall_rating})>"


class MLBLineupSlot(UUIDPrimaryKeyMixin, Base):
    """
    MLB The Show 26 lineup slot — a single position in a batting order.
    """

    __tablename__ = "mlb_lineup_slots"

    lineup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mlb_lineups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mlb_players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batting_order: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    lineup: Mapped["MLBLineup"] = relationship(back_populates="slots")
    player: Mapped["MLBPlayer"] = relationship(back_populates="lineup_slots")

    def __repr__(self) -> str:
        return f"<MLBLineupSlot order={self.batting_order}>"
