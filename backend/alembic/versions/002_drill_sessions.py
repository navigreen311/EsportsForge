"""Drill execution sessions + per-rep tracking.

Revision ID: 002
Revises: 001
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drill_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("drill_id", sa.String(length=100), nullable=False),
        sa.Column("drill_type", sa.String(length=100), nullable=True),
        sa.Column("title_id", sa.String(length=50), nullable=False),
        sa.Column("total_reps", sa.Integer(), nullable=False),
        sa.Column("completed_reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fail_reps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("auto_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_drill_sessions_user_id", "drill_sessions", ["user_id"])

    op.create_table(
        "drill_reps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "drill_session_id",
            sa.String(length=36),
            sa.ForeignKey("drill_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rep_number", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("auto_detected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_drill_reps_drill_session_id", "drill_reps", ["drill_session_id"])


def downgrade() -> None:
    op.drop_index("ix_drill_reps_drill_session_id", table_name="drill_reps")
    op.drop_table("drill_reps")
    op.drop_index("ix_drill_sessions_user_id", table_name="drill_sessions")
    op.drop_table("drill_sessions")
