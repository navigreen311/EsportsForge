"""add recommendation feedback_at column

Revision ID: rec_20260505_0001
Revises: af_20260504_0001
Create Date: 2026-05-05

Adds a ``feedback_at`` timestamp to the ``recommendations`` table so the
follow/dismiss feedback flow recorded by the dashboard can persist when the
player submitted their reaction. Idempotent against sqlite + postgres.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "rec_20260505_0001"
down_revision: Union[str, None] = "af_20260504_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add feedback_at column if it does not already exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "recommendations" not in set(inspector.get_table_names()):
        return

    existing_cols = {col["name"] for col in inspector.get_columns("recommendations")}
    if "feedback_at" in existing_cols:
        return

    op.add_column(
        "recommendations",
        sa.Column("feedback_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "recommendations" not in set(inspector.get_table_names()):
        return

    existing_cols = {col["name"] for col in inspector.get_columns("recommendations")}
    if "feedback_at" not in existing_cols:
        return

    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.drop_column("feedback_at")
