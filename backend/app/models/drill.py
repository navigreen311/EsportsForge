"""Drill model — DrillBot training exercises."""

import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class Drill(UUIDPrimaryKeyMixin, Base):
    """
    DrillBot drill — a targeted training exercise for skill development.
    """

    __tablename__ = "drills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title"
    )
    skill_target: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Skill being trained"
    )
    difficulty_level: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g. beginner, intermediate, advanced"
    )
    drill_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Configuration parameters for the drill"
    )
    completion_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    success_rate: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="Ratio of successful completions"
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="drills")

    def __repr__(self) -> str:
        return f"<Drill {self.skill_target} ({self.difficulty_level})>"
