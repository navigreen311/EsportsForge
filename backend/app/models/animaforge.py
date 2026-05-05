"""AnimaForge integration — render-job tracking.

Every render request submitted to AnimaForge gets a row here, including
failed ones (so the UI can show retry state). Successful jobs hold the
videoUrl/thumbnailUrl that completed renders are served from.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Job types — must match values sent to AnimaForge `/api/v1/render`
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Job status — string column (kept loose for forward-compat with AnimaForge)
# ---------------------------------------------------------------------------
STATUS_PENDING = "pending"
STATUS_RENDERING = "rendering"
STATUS_COMPLETE = "complete"
STATUS_FAILED = "failed"


# Special user_id used for shared (non-personalized) renders, e.g. drill demos.
SYSTEM_USER_ID = "system"


class AnimaForgeJob(UUIDPrimaryKeyMixin, Base):
    """Tracks every render job submitted to AnimaForge.

    `source_id` encoding (per contract §2):
      * weapon: ``source_id = weapon_id`` (uuid)
      * drill:  ``source_id = f"{title_id}:{drill_type}"``  (shared, ``user_id="system"``)
      * play:   ``source_id = f"{play_id}:{coverage}"``     (per-coverage variant)
      * share:  ``source_id = f"{trigger_type}:{session_id_or_milestone_key}"``
    """

    __tablename__ = "animaforge_jobs"

    # NOTE: foreign key intentionally omitted — `user_id` may be the literal
    # string ``"system"`` for shared renders (drill demos), which would violate
    # an FK constraint against ``users.id``. The contract explicitly allows it.
    user_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
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
