"""Drill execution session — per-attempt rep tracking with auto-detection.

A `DrillSession` is one player's attempt at a configured drill. It contains
N `DrillRep` rows, one per scheduled rep, each marked success/fail either
manually or by the VisionAudioForge auto-detector.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class DrillSession(UUIDPrimaryKeyMixin, Base):
    """A single attempt at a drill — N reps logged in :class:`DrillRep`."""

    __tablename__ = "drill_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    drill_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Client-side drill identifier (e.g. 'drill-1' or a UUID).",
    )
    drill_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Detection-config key (e.g. 'pre-snap-reads').",
    )
    title_id: Mapped[str] = mapped_column(String(50), nullable=False)
    total_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
        comment="active | complete | abandoned",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship()
    reps: Mapped[list["DrillRep"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DrillRep.rep_number",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<DrillSession {self.id} {self.drill_id} "
            f"{self.completed_reps}/{self.total_reps}>"
        )


class DrillRep(UUIDPrimaryKeyMixin, Base):
    """A single rep within a :class:`DrillSession`."""

    __tablename__ = "drill_reps"

    drill_session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("drill_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rep_number: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    auto_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Detector confidence 0-1."
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Detector or player explanation.",
    )

    session: Mapped["DrillSession"] = relationship(back_populates="reps")

    def __repr__(self) -> str:
        outcome = "✓" if self.success else "✗"
        return f"<DrillRep #{self.rep_number} {outcome}>"
