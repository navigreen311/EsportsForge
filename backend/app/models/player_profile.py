"""PlayerTwin profile model — the AI-generated competitive identity."""

import enum
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class InputType(str, enum.Enum):
    """Physical input device used by the player."""

    CONTROLLER = "controller"
    KBM = "kbm"
    FIGHTSTICK = "fightstick"


class PlayerProfile(UUIDPrimaryKeyMixin, Base):
    """
    PlayerTwin — AI-generated competitive identity profile.

    Stores the player's tendencies, execution ceiling, panic patterns,
    and core identity traits derived from game session analysis.
    """

    __tablename__ = "player_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Game title this profile is for"
    )
    tendencies: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Behavioral tendencies extracted from gameplay"
    )
    execution_ceiling: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Max skill metrics across categories"
    )
    panic_patterns: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Patterns observed under pressure"
    )
    identity: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Core identity: risk_tolerance, aggression, pace, style",
    )
    input_type: Mapped[InputType] = mapped_column(
        Enum(InputType, name="input_type", native_enum=True),
        default=InputType.CONTROLLER,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="player_profile")

    def __repr__(self) -> str:
        return f"<PlayerProfile user_id={self.user_id} title={self.title}>"
