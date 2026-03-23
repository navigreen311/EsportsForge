"""User model for EsportsForge accounts."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.drill import Drill
    from app.models.game_session import GameSession
    from app.models.gameplan import Gameplan
    from app.models.impact_ranking import ImpactRanking
    from app.models.integrity_mode import IntegrityMode
    from app.models.player_profile import PlayerProfile
    from app.models.recommendation import Recommendation


class UserRole(str, enum.Enum):
    """Subscription tiers for EsportsForge."""

    FREE = "free"
    COMPETITIVE = "competitive"
    ELITE = "elite"
    TEAM = "team"


class User(UUIDPrimaryKeyMixin, Base):
    """EsportsForge user account."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True),
        default=UserRole.FREE,
        nullable=False,
    )
    active_title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Currently active game title"
    )

    # Relationships
    player_profile: Mapped[Optional["PlayerProfile"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    game_sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    gameplans: Mapped[list["Gameplan"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    impact_rankings: Mapped[list["ImpactRanking"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    drills: Mapped[list["Drill"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    integrity_mode: Mapped[Optional["IntegrityMode"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
