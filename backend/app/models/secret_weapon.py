"""Secret Weapon Arsenal — multi-title weapon library models.

Three tables:
  - SecretWeapon       — platform / user / web-discovered weapons
  - WeaponUsageLog     — every deploy / outcome record
  - UserArsenal        — saved-weapon join table (user <-> weapon)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

# Canonical title IDs used everywhere — keep in sync with the frontend
# titleMeta constants and the existing per-title schemas.
TITLE_IDS: tuple[str, ...] = (
    "madden-26",
    "cfb-26",
    "nba-2k26",
    "eafc-26",
    "mlb-26",
    "warzone",
    "fortnite",
    "ufc-5",
    "pga-2k25",
    "undisputed",
    "video-poker",
)


class SecretWeapon(UUIDPrimaryKeyMixin, Base):
    """A trick play, unstoppable concept, or situational exploit."""

    __tablename__ = "secret_weapons"

    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    sub_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    formation: Mapped[str | None] = mapped_column(String(120), nullable=True)
    play_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    setup_steps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    when_to_use: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_conditions: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    title_specific_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    times_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    patch_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(32), default="platform", nullable=False
    )  # "platform" | "user-upload" | "web-discovery"
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    community_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    community_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WeaponUsageLog(UUIDPrimaryKeyMixin, Base):
    """Every time a saved weapon is deployed (or skipped) in a session."""

    __tablename__ = "weapon_usage_log"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weapon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("secret_weapons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    game_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    deployed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    worked: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    opponent_adjusted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserArsenal(Base):
    """Join table — which weapons a user has saved into their personal arsenal."""

    __tablename__ = "user_arsenal"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weapon_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("secret_weapons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "weapon_id", name="uq_user_arsenal_user_weapon"),
    )
