"""GamePatch + MetaAlert tables for GameplanAI meta context.

Revision ID: 003
Revises: 002
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "game_patches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("title_id", sa.String(length=50), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_game_patches_title_id", "game_patches", ["title_id"])
    op.create_index("ix_game_patches_title_release", "game_patches", ["title_id", "release_date"])

    op.create_table(
        "meta_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("title_id", sa.String(length=50), nullable=False),
        sa.Column("patch_version", sa.String(length=50), nullable=True),
        sa.Column("weapon_name", sa.String(length=200), nullable=False),
        sa.Column("weapon_why", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="published"),
        sa.Column("direction", sa.String(length=20), nullable=False, server_default="strong"),
        sa.Column("countered_concepts", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_meta_alerts_title_id", "meta_alerts", ["title_id"])


def downgrade() -> None:
    op.drop_index("ix_meta_alerts_title_id", table_name="meta_alerts")
    op.drop_table("meta_alerts")
    op.drop_index("ix_game_patches_title_release", table_name="game_patches")
    op.drop_index("ix_game_patches_title_id", table_name="game_patches")
    op.drop_table("game_patches")
