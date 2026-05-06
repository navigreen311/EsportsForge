"""add daily forge tables

Revision ID: df_20260505_0001
Revises: af_20260504_0001
Create Date: 2026-05-05

Hand-written migration. Creates the ``daily_forge_completions`` and
``daily_forge_streaks`` tables used by the Daily Forge dashboard card to
persist per-day mission completions and per-user streak counters.

Idempotent against repeated `alembic upgrade head` runs (common when the
SQLite dev DB has already been auto-created via `Base.metadata.create_all`
during app lifespan).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "df_20260505_0001"
down_revision: Union[str, None] = "af_20260504_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create daily_forge_completions + daily_forge_streaks tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "daily_forge_completions" not in existing_tables:
        op.create_table(
            "daily_forge_completions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(length=36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column(
                "drill_done",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "focus_done",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "mental_done",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column(
                "meta_done",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
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
            sa.UniqueConstraint(
                "user_id", "date", name="uq_daily_forge_completions_user_date"
            ),
        )
        op.create_index(
            "ix_daily_forge_completions_user_id",
            "daily_forge_completions",
            ["user_id"],
        )
        op.create_index(
            "ix_daily_forge_completions_date",
            "daily_forge_completions",
            ["date"],
        )

    if "daily_forge_streaks" not in existing_tables:
        op.create_table(
            "daily_forge_streaks",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(length=36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column(
                "current_streak",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column("last_completed_date", sa.Date(), nullable=True),
            sa.Column(
                "longest_streak",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
            ),
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
            "ix_daily_forge_streaks_user_id",
            "daily_forge_streaks",
            ["user_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "daily_forge_streaks" in existing_tables:
        try:
            op.drop_index(
                "ix_daily_forge_streaks_user_id",
                table_name="daily_forge_streaks",
            )
        except Exception:  # noqa: BLE001
            pass
        op.drop_table("daily_forge_streaks")

    if "daily_forge_completions" in existing_tables:
        for ix in (
            "ix_daily_forge_completions_date",
            "ix_daily_forge_completions_user_id",
        ):
            try:
                op.drop_index(ix, table_name="daily_forge_completions")
            except Exception:  # noqa: BLE001
                pass
        op.drop_table("daily_forge_completions")
