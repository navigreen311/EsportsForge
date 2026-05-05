"""add animaforge jobs

Revision ID: af_20260504_0001
Revises: 001
Create Date: 2026-05-04

Hand-written migration. Creates the ``animaforge_jobs`` table used by the
AnimaForge integration to track render jobs (per contract §2).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "af_20260504_0001"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create animaforge_jobs table (idempotent against sqlite + postgres)."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "animaforge_jobs" in existing_tables:
        return

    op.create_table(
        "animaforge_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("title_id", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("spec", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_animaforge_jobs_user_id", "animaforge_jobs", ["user_id"]
    )
    op.create_index(
        "ix_animaforge_jobs_job_id", "animaforge_jobs", ["job_id"], unique=True
    )
    op.create_index(
        "ix_animaforge_jobs_type", "animaforge_jobs", ["type"]
    )
    op.create_index(
        "ix_animaforge_jobs_source_id", "animaforge_jobs", ["source_id"]
    )
    op.create_index(
        "ix_animaforge_jobs_title_id", "animaforge_jobs", ["title_id"]
    )
    op.create_index(
        "ix_animaforge_jobs_status", "animaforge_jobs", ["status"]
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "animaforge_jobs" not in set(inspector.get_table_names()):
        return

    for ix in (
        "ix_animaforge_jobs_status",
        "ix_animaforge_jobs_title_id",
        "ix_animaforge_jobs_source_id",
        "ix_animaforge_jobs_type",
        "ix_animaforge_jobs_job_id",
        "ix_animaforge_jobs_user_id",
    ):
        try:
            op.drop_index(ix, table_name="animaforge_jobs")
        except Exception:  # noqa: BLE001 — best-effort cleanup
            pass

    op.drop_table("animaforge_jobs")
