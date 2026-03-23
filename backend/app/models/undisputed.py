"""Undisputed specific models — fighters, fights, and career progression."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class FighterArchetype(str, enum.Enum):
    """Boxing archetype classification."""
    SWARMER = "swarmer"
    OUT_BOXER = "out_boxer"
    SLUGGER = "slugger"
    COUNTER_PUNCHER = "counter_puncher"
    BOXER_PUNCHER = "boxer_puncher"
    SWITCH_HITTER = "switch_hitter"


class FighterStance(str, enum.Enum):
    """Boxing stance."""
    ORTHODOX = "orthodox"
    SOUTHPAW = "southpaw"


class UndisputedFighter(UUIDPrimaryKeyMixin, Base):
    """
    Undisputed fighter — a created or saved fighter profile.

    Stores attributes, archetype, stance, and career data.
    """

    __tablename__ = "undisputed_fighters"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    weight_class: Mapped[str] = mapped_column(String(50), nullable=False)
    archetype: Mapped[FighterArchetype] = mapped_column(
        Enum(FighterArchetype, name="fighter_archetype", native_enum=True), nullable=False
    )
    stance: Mapped[FighterStance] = mapped_column(
        Enum(FighterStance, name="fighter_stance", native_enum=True), nullable=False
    )
    overall: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Full attribute breakdown: power, speed, chin, stamina, etc."
    )
    career_record: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="W-L-D record and KO stats"
    )
    punch_package: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Equipped punch package loadout"
    )

    # Relationships
    fights: Mapped[list["UndisputedFight"]] = relationship(
        back_populates="fighter", lazy="selectin", cascade="all, delete-orphan",
        foreign_keys="UndisputedFight.fighter_id",
    )

    def __repr__(self) -> str:
        return f"<UndisputedFighter {self.name} ({self.archetype.value})>"


class UndisputedFight(UUIDPrimaryKeyMixin, Base):
    """
    Undisputed fight — a completed or scheduled fight record.

    Stores round-by-round scoring, damage data, and fight result.
    """

    __tablename__ = "undisputed_fights"

    fighter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("undisputed_fighters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opponent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    opponent_archetype: Mapped[str] = mapped_column(String(50), nullable=False)
    rounds_scheduled: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    result: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, comment="win, loss, draw, ko_win, ko_loss, tko_win, tko_loss"
    )
    rounds_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scorecard: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Round-by-round scorecard data"
    )
    damage_timeline: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Round-by-round damage accumulation"
    )
    fight_stats: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Aggregate fight statistics"
    )

    # Relationships
    fighter: Mapped["UndisputedFighter"] = relationship(
        back_populates="fights", foreign_keys=[fighter_id]
    )

    def __repr__(self) -> str:
        return f"<UndisputedFight vs {self.opponent_name} ({self.result})>"
