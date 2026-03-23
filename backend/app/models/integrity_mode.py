"""IntegrityMode model — ethical AI usage settings per environment."""

import enum
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class GameEnvironment(str, enum.Enum):
    """Competitive environment context."""

    OFFLINE_LAB = "offline_lab"
    RANKED = "ranked"
    TOURNAMENT = "tournament"
    BROADCAST = "broadcast"


class AntiCheatStatus(str, enum.Enum):
    """Anti-cheat compliance status."""

    COMPLIANT = "compliant"
    WARNING = "warning"
    RESTRICTED = "restricted"


class IntegrityMode(UUIDPrimaryKeyMixin, Base):
    """
    IntegrityMode — per-user ethical AI settings.

    Controls which features are available based on competitive environment
    to ensure fair play and tournament compliance.
    """

    __tablename__ = "integrity_modes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    environment: Mapped[GameEnvironment] = mapped_column(
        Enum(GameEnvironment, name="game_environment", native_enum=True),
        default=GameEnvironment.OFFLINE_LAB,
        nullable=False,
    )
    restricted_features: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Features disabled in current environment"
    )
    anti_cheat_status: Mapped[AntiCheatStatus] = mapped_column(
        Enum(AntiCheatStatus, name="anti_cheat_status", native_enum=True),
        default=AntiCheatStatus.COMPLIANT,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="integrity_mode")

    def __repr__(self) -> str:
        return f"<IntegrityMode {self.environment.value} ({self.anti_cheat_status.value})>"
