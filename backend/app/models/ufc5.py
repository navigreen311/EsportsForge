"""UFC 5 specific models — fighters, rounds, and fight intelligence."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class WeightClass(str, enum.Enum):
    """UFC weight class divisions."""

    STRAWWEIGHT = "strawweight"
    FLYWEIGHT = "flyweight"
    BANTAMWEIGHT = "bantamweight"
    FEATHERWEIGHT = "featherweight"
    LIGHTWEIGHT = "lightweight"
    WELTERWEIGHT = "welterweight"
    MIDDLEWEIGHT = "middleweight"
    LIGHT_HEAVYWEIGHT = "light_heavyweight"
    HEAVYWEIGHT = "heavyweight"
    WOMENS_STRAWWEIGHT = "womens_strawweight"
    WOMENS_FLYWEIGHT = "womens_flyweight"
    WOMENS_BANTAMWEIGHT = "womens_bantamweight"
    WOMENS_FEATHERWEIGHT = "womens_featherweight"


class FightResult(str, enum.Enum):
    """Possible fight outcomes."""

    KO = "ko"
    TKO = "tko"
    SUBMISSION = "submission"
    DECISION_UNANIMOUS = "decision_unanimous"
    DECISION_SPLIT = "decision_split"
    DECISION_MAJORITY = "decision_majority"
    DQ = "dq"
    NO_CONTEST = "no_contest"


class UFCFighter(UUIDPrimaryKeyMixin, Base):
    """
    UFC 5 fighter profile — stores build, archetype, and career stats.

    Links to round-level performance data for fight intelligence.
    """

    __tablename__ = "ufc_fighters"

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    weight_class: Mapped[WeightClass] = mapped_column(
        Enum(WeightClass, name="ufc_weight_class", native_enum=True),
        nullable=False,
    )
    archetype: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Primary fighting style archetype"
    )
    overall_rating: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Fighter overall rating 0-100"
    )
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Attribute ratings (striking, grappling, etc.)"
    )
    perks: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Equipped perks and their tiers"
    )
    career_stats: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Win/loss record, finish rates, etc."
    )

    # Relationships
    rounds: Mapped[list["UFCRound"]] = relationship(
        back_populates="fighter", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UFCFighter {self.name} ({self.weight_class.value})>"


class UFCRound(UUIDPrimaryKeyMixin, Base):
    """
    UFC 5 round-level fight data — damage, stamina, scoring.

    Captures per-round metrics for judge-aware scoring and stamina economy analysis.
    """

    __tablename__ = "ufc_rounds"

    fighter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ufc_fighters.id", ondelete="CASCADE"),
        nullable=False,
    )
    fight_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="Unique identifier for the fight this round belongs to",
    )
    round_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    score_player: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, comment="Player judge score"
    )
    score_opponent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=9, comment="Opponent judge score"
    )
    significant_strikes_landed: Mapped[int] = mapped_column(
        Integer, default=0
    )
    significant_strikes_absorbed: Mapped[int] = mapped_column(
        Integer, default=0
    )
    takedowns_landed: Mapped[int] = mapped_column(Integer, default=0)
    takedowns_defended: Mapped[int] = mapped_column(Integer, default=0)
    control_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    knockdowns_scored: Mapped[int] = mapped_column(Integer, default=0)
    stamina_end: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Stamina % at end of round"
    )
    damage_state: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Cumulative damage state snapshot"
    )
    result: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Round result if fight ended (KO, TKO, SUB, etc.)",
    )

    # Relationships
    fighter: Mapped["UFCFighter"] = relationship(back_populates="rounds")

    def __repr__(self) -> str:
        return f"<UFCRound fight={self.fight_id} R{self.round_number}>"
