"""Warzone models — loadouts, matches, and combat intelligence persistence."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class WeaponClassEnum(str, enum.Enum):
    """Weapon class categories persisted in DB."""

    ASSAULT_RIFLE = "assault_rifle"
    SMG = "smg"
    LMG = "lmg"
    SNIPER = "sniper"
    MARKSMAN = "marksman"
    SHOTGUN = "shotgun"
    PISTOL = "pistol"
    LAUNCHER = "launcher"
    MELEE = "melee"


class WarzoneLoadout(UUIDPrimaryKeyMixin, Base):
    """
    A saved Warzone loadout build.

    Stores primary/secondary weapon configs, perks, and effectiveness metrics.
    """

    __tablename__ = "warzone_loadouts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    primary_weapon: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    primary_class: Mapped[WeaponClassEnum] = mapped_column(
        Enum(WeaponClassEnum, name="wz_weapon_class", native_enum=True),
        nullable=False,
    )
    primary_attachments: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Attachment config for primary weapon"
    )
    secondary_weapon: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    secondary_class: Mapped[WeaponClassEnum] = mapped_column(
        Enum(WeaponClassEnum, name="wz_weapon_class_secondary", native_enum=True),
        nullable=False,
    )
    secondary_attachments: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Attachment config for secondary weapon"
    )
    perks: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Perk package selection"
    )
    tactical: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stun_grenade"
    )
    lethal: Mapped[str] = mapped_column(
        String(50), nullable=False, default="semtex"
    )
    effectiveness_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    meta_tier: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True, comment="S/A/B/C/D tier rating"
    )

    # Relationships
    matches: Mapped[list["WarzoneMatch"]] = relationship(
        back_populates="loadout", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WarzoneLoadout {self.name} ({self.primary_weapon}/{self.secondary_weapon})>"


class WarzoneMatch(UUIDPrimaryKeyMixin, Base):
    """
    A Warzone match record with performance metrics.

    Captures placement, kills, damage, and zone/rotation intelligence.
    """

    __tablename__ = "warzone_matches"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    loadout_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("warzone_loadouts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    map_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="urzikstan"
    )
    placement: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    kills: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    deaths: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    damage_dealt: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    squad_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4
    )
    zone_rotations: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Zone rotation path data"
    )
    engagement_log: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Fight-by-fight engagement data"
    )
    gulag_result: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="'won', 'lost', or null if no gulag"
    )

    # Relationships
    loadout: Mapped[Optional["WarzoneLoadout"]] = relationship(
        back_populates="matches"
    )

    def __repr__(self) -> str:
        return f"<WarzoneMatch #{self.placement} — {self.kills}K/{self.deaths}D>"
