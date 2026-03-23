"""ImpactRank model — prioritized weakness tracking."""

import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class ImpactStatus(str, enum.Enum):
    """Lifecycle status of an identified weakness."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    DEFERRED = "deferred"


class ImpactRanking(UUIDPrimaryKeyMixin, Base):
    """
    ImpactRank — a prioritized weakness with estimated win-rate impact.

    Surfaces what to fix first for maximum competitive gain.
    """

    __tablename__ = "impact_rankings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title"
    )
    weakness_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Canonical weakness identifier"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Human-readable weakness description"
    )
    win_rate_damage: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Estimated win-rate cost of this weakness"
    )
    fix_priority: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Lower = fix first"
    )
    expected_lift: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Expected win-rate improvement if fixed"
    )
    time_to_master: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Estimated time to resolve e.g. '2 weeks'"
    )
    status: Mapped[ImpactStatus] = mapped_column(
        Enum(ImpactStatus, name="impact_status", native_enum=True),
        default=ImpactStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="impact_rankings")

    def __repr__(self) -> str:
        return f"<ImpactRanking P{self.fix_priority}: {self.description[:40]}>"
