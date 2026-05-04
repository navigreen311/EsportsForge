"""MetaAlert + GamePatch — current-meta context surfaced to GameplanAI."""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class GamePatch(UUIDPrimaryKeyMixin, Base):
    """A patch / title-update version for a given title."""

    __tablename__ = "game_patches"

    title_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_game_patches_title_release", "title_id", "release_date"),
    )

    def __repr__(self) -> str:
        return f"<GamePatch {self.title_id}@{self.version}>"


class MetaAlert(UUIDPrimaryKeyMixin, Base):
    """A current-meta callout — what to use, what to avoid, what's countered.

    Read by GameplanAI when building a plan so plays can be tagged
    `isTrendingCountered` and the meta_status reflects the live patch.
    """

    __tablename__ = "meta_alerts"

    title_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    patch_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    weapon_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="The play / weapon / scheme this alert is about.",
    )
    weapon_why: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="One paragraph explaining why this is meta right now.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
        comment="draft | published | retired",
    )
    direction: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="strong",
        comment="strong | exploit | countered | watching",
    )
    countered_concepts: Mapped[Optional[list]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tags/play names this alert flags as currently countered.",
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<MetaAlert {self.title_id} {self.weapon_name} ({self.direction})>"
