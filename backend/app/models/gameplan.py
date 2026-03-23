"""Gameplan model — strategic play-calling sheets."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.opponent import Opponent
    from app.models.user import User


class Gameplan(UUIDPrimaryKeyMixin, Base):
    """
    A strategic gameplan containing plays, kill sheets, and meta snapshots.

    Can be opponent-specific or general-purpose.
    """

    __tablename__ = "gameplans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Gameplan name"
    )
    opponent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opponents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plays: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JSON, nullable=True, comment="Ordered list of play calls"
    )
    kill_sheet: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Opponent-specific exploit sheet"
    )
    meta_snapshot: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Current meta context when plan was created"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When this plan becomes stale"
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="gameplans")
    opponent: Mapped[Optional["Opponent"]] = relationship(lazy="selectin")

    def __repr__(self) -> str:
        return f"<Gameplan {self.title}>"
