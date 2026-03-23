"""NBA 2K26 specific models — builds, plays, MyTeam data."""

import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class NBA2KPosition(str, enum.Enum):
    """NBA 2K26 player position."""

    PG = "pg"
    SG = "sg"
    SF = "sf"
    PF = "pf"
    C = "c"


class NBA2KArchetype(str, enum.Enum):
    """NBA 2K26 build archetype."""

    SHOT_CREATOR = "shot_creator"
    SLASHER = "slasher"
    STRETCH = "stretch"
    GLASS_CLEANER = "glass_cleaner"
    PLAYMAKER = "playmaker"
    LOCKDOWN = "lockdown"
    TWO_WAY = "two_way"
    INSIDE_BIG = "inside_big"
    SHARPSHOOTER = "sharpshooter"
    POST_SCORER = "post_scorer"


class NBA2KBuild(UUIDPrimaryKeyMixin, Base):
    """
    NBA 2K26 player build — stores attribute allocation, badge setup, and meta tier.

    Represents a user's MyPlayer build with all attribute breakdowns.
    """

    __tablename__ = "nba2k_builds"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[NBA2KPosition] = mapped_column(
        Enum(NBA2KPosition, name="nba2k_position", native_enum=True), nullable=False, index=True
    )
    archetype: Mapped[NBA2KArchetype] = mapped_column(
        Enum(NBA2KArchetype, name="nba2k_archetype", native_enum=True), nullable=False, index=True
    )
    height_inches: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_lbs: Mapped[int] = mapped_column(Integer, nullable=False)
    wingspan_inches: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_rating: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False, index=True
    )
    attributes: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Full attribute breakdown (close_shot, driving_layup, etc.)"
    )
    badges: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Badge allocation by category"
    )
    meta_tier: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Current meta tier classification"
    )

    # Relationships
    plays: Mapped[list["NBA2KPlay"]] = relationship(
        back_populates="build", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NBA2KBuild {self.name} ({self.position.value} {self.archetype.value})>"


class NBA2KPlayType(str, enum.Enum):
    """Play type classification."""

    PICK_AND_ROLL = "pick_and_roll"
    ISOLATION = "isolation"
    POST_UP = "post_up"
    FAST_BREAK = "fast_break"
    SPOT_UP = "spot_up"
    OFF_SCREEN = "off_screen"
    CUT = "cut"
    HANDOFF = "handoff"


class NBA2KPlay(UUIDPrimaryKeyMixin, Base):
    """NBA 2K26 recorded play — game session data for analysis."""

    __tablename__ = "nba2k_plays"

    build_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("nba2k_builds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    game_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    play_type: Mapped[NBA2KPlayType] = mapped_column(
        Enum(NBA2KPlayType, name="nba2k_play_type", native_enum=True),
        nullable=False,
        index=True,
    )
    result: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="made, missed, turnover, assist, etc."
    )
    points_scored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shot_quality: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="0.0-1.0 shot quality rating"
    )
    defender_contest: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False, comment="0.0-1.0 contest level"
    )
    play_details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional play metadata (dribble moves, timing, etc.)"
    )

    # Relationships
    build: Mapped["NBA2KBuild"] = relationship(back_populates="plays")

    def __repr__(self) -> str:
        return f"<NBA2KPlay {self.play_type.value} -> {self.result}>"
