"""EA FC 26 specific models — squads, formations, and card tracking."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class CardTier(str, enum.Enum):
    """Card tier classification in EA FC 26."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    RARE_GOLD = "rare_gold"
    TOTW = "totw"
    HERO = "hero"
    ICON = "icon"
    TOTY = "toty"
    TOTS = "tots"


class EAFCSquad(UUIDPrimaryKeyMixin, Base):
    """
    EA FC 26 squad — a saved squad configuration.

    Stores formation, chemistry score, and all squad slot data.
    """

    __tablename__ = "eafc_squads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True
    )
    formation: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    chemistry_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    total_value: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    average_overall: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    slots: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Squad slot data: position -> card info"
    )

    # Relationships
    formation_ref: Mapped[Optional["EAFCFormation"]] = relationship(
        back_populates="squads",
        primaryjoin="foreign(EAFCSquad.formation) == EAFCFormation.name",
        lazy="selectin",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<EAFCSquad {self.name} ({self.formation})>"


class EAFCFormation(UUIDPrimaryKeyMixin, Base):
    """
    EA FC 26 formation — meta tracking for formation effectiveness.

    Tracks usage rates, win rates, and meta rating per patch.
    """

    __tablename__ = "eafc_formations"

    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    rating: Mapped[str] = mapped_column(
        String(5), nullable=False, comment="S, A, B, C, D"
    )
    usage_pct: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    win_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    patch_version: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    positions: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Ordered list of positions in this formation"
    )
    meta_notes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Strengths, weaknesses, and playstyle notes"
    )

    # Relationships
    squads: Mapped[list["EAFCSquad"]] = relationship(
        back_populates="formation_ref",
        primaryjoin="EAFCFormation.name == foreign(EAFCSquad.formation)",
        lazy="selectin",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<EAFCFormation {self.name} ({self.rating})>"
