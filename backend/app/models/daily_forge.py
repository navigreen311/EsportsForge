"""Daily Forge persistence — per-day completion + streak tracking.

The Daily Forge dashboard card has 4 mission items (drill / focus / mental cue
/ meta tip). Each item can be checked off independently. When all 4 become
true on the same day, the user earns a "completion" — `completed_at` is
stamped, the streak advances, and a banner is shown.

Two tables:
  * ``daily_forge_completions`` — one row per (user, date), holds the 4 flags.
  * ``daily_forge_streaks`` — one row per user, current/longest streak counts.
"""

from __future__ import annotations

import uuid
from datetime import date as _date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class DailyForgeCompletion(UUIDPrimaryKeyMixin, Base):
    """One row per (user, date) — tracks the 4 daily mission flags."""

    __tablename__ = "daily_forge_completions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "date", name="uq_daily_forge_completions_user_date"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[_date] = mapped_column(Date, nullable=False, index=True)
    drill_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    focus_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mental_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    meta_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def all_complete(self) -> bool:
        return bool(
            self.drill_done and self.focus_done and self.mental_done and self.meta_done
        )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DailyForgeCompletion user={self.user_id} date={self.date}>"


class DailyForgeStreak(UUIDPrimaryKeyMixin, Base):
    """Per-user streak counter."""

    __tablename__ = "daily_forge_streaks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    current_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_completed_date: Mapped[Optional[_date]] = mapped_column(
        Date, nullable=True
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DailyForgeStreak user={self.user_id} "
            f"current={self.current_streak} longest={self.longest_streak}>"
        )
