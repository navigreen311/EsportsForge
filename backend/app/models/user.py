"""User model for EsportsForge accounts."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
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


# Alias used by auth/security modules
UserTier = UserRole

TIER_TITLE_LIMITS: dict[UserRole, int | None] = {
    UserRole.FREE: 1,
    UserRole.COMPETITIVE: 3,
    UserRole.ELITE: 6,
    UserRole.TEAM: None,
}


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
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.FREE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    active_title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Currently active game title"
    )
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    two_factor_secret: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
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

    @property
    def tier(self) -> str:
        """Alias for role — used by auth and API responses."""
        return self.role.value if self.role else UserRole.FREE.value

    @tier.setter
    def tier(self, value: "UserRole") -> None:
        self.role = value

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
