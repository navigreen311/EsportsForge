"""Game session model — individual match/session records."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.opponent import Opponent
    from app.models.recommendation import Recommendation
    from app.models.user import User


class GameMode(str, enum.Enum):
    """Type of competitive session."""

    RANKED = "ranked"
    TOURNAMENT = "tournament"
    TRAINING = "training"


class GameResult(str, enum.Enum):
    """Outcome of a game session."""

    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


class GameSession(UUIDPrimaryKeyMixin, Base):
    """A single game session or match record."""

    __tablename__ = "game_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title"
    )
    mode: Mapped[GameMode] = mapped_column(
        Enum(GameMode, name="game_mode", native_enum=True), nullable=False
    )
    opponent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opponents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    result: Mapped[GameResult] = mapped_column(
        Enum(GameResult, name="game_result", native_enum=True), nullable=False
    )
    stats: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Raw game stats blob"
    )
    recommendations_followed: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Which recommendations were applied"
    )
    session_duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Duration in seconds"
    )
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="game_sessions")
    opponent: Mapped[Optional["Opponent"]] = relationship(lazy="selectin")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="session", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<GameSession {self.id} {self.result.value} on {self.title}>"
