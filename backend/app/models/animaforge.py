# STUB — replace at merge.
#
# Agent #1 owns the canonical AnimaForgeJob model (see
# `docs/integrations/animaforge_contract.md` Section 2).  This stub exists
# ONLY so Agent #6's drill endpoint can import the model and constants
# without depending on Agent #1's branch being merged first.
#
# At merge, replace with Agent #1's version. The columns and constants
# below match the contract surface used by all consumers.
"""AnimaForge integration — render-job tracking (stub)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


# ── Job types ───────────────────────────────────────────────────────────
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

# ── Job status ──────────────────────────────────────────────────────────
STATUS_PENDING = "pending"
STATUS_RENDERING = "rendering"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"


class AnimaForgeJob(UUIDPrimaryKeyMixin, Base):
    """Tracks every render job submitted to AnimaForge."""

    __tablename__ = "animaforge_jobs"

    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )  # "system" for shared (drill) renders
    job_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
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


__all__ = [
    "AnimaForgeJob",
    "JOB_TYPE_WEAPON",
    "JOB_TYPE_DRILL",
    "JOB_TYPE_PLAY",
    "JOB_TYPE_SHARE",
    "JOB_TYPES",
    "STATUS_PENDING",
    "STATUS_RENDERING",
    "STATUS_COMPLETE",
    "STATUS_FAILED",
]
