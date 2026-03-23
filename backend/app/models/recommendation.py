"""ForgeCore recommendation model — AI-generated coaching suggestions."""

import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.game_session import GameSession
    from app.models.user import User


class Recommendation(UUIDPrimaryKeyMixin, Base):
    """
    ForgeCore recommendation — an AI-generated coaching suggestion.

    Tracks accuracy and impact for the Truth Engine audit system.
    """

    __tablename__ = "recommendations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_source: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Which AI agent generated this"
    )
    recommendation_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Category of recommendation"
    )
    content: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="Full recommendation payload"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Agent confidence 0.0-1.0"
    )
    impact_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Measured impact after follow-through"
    )
    was_followed: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="Did the player follow this?"
    )
    outcome_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="Was the prediction correct?"
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="recommendations")
    session: Mapped[Optional["GameSession"]] = relationship(
        back_populates="recommendations"
    )

    def __repr__(self) -> str:
        return f"<Recommendation {self.recommendation_type} conf={self.confidence_score:.2f}>"
