"""AnimaForge integration — render-job tracking.

# STUB FOR BRANCH-LOCAL TEST — Agent #1's version will replace this at merge

This minimal stub mirrors the canonical AnimaForgeJob shape from the contract
(docs/integrations/animaforge_contract.md §2) so Agent #2's webhook + tests
can run on this branch in isolation. The merge coordinator MUST delete this
file before merging Agent #2's branch — Agent #1's branch owns the canonical
version with the full SQLAlchemy JSON column for ``spec``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


# Job types
JOB_TYPE_WEAPON = "weapon-diagram"
JOB_TYPE_DRILL = "drill-demo"
JOB_TYPE_PLAY = "play-diagram"
JOB_TYPE_SHARE = "share-win"
JOB_TYPES: tuple[str, ...] = (
    JOB_TYPE_WEAPON,
    JOB_TYPE_DRILL,
    JOB_TYPE_PLAY,
    JOB_TYPE_SHARE,
)

# Job status
STATUS_PENDING = "pending"
STATUS_RENDERING = "rendering"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"

TERMINAL_STATUSES: tuple[str, ...] = (STATUS_COMPLETE, STATUS_FAILED)


class AnimaForgeJob(UUIDPrimaryKeyMixin, Base):
    """Tracks every render job submitted to AnimaForge."""

    __tablename__ = "animaforge_jobs"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    job_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )  # AnimaForge's external id
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=STATUS_PENDING, index=True
    )
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spec: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
