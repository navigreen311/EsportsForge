"""add arsenal voice settings to identity profile

Revision ID: avs_20260516_0001
Revises: ffa2cd90434a
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "avs_20260516_0001"
down_revision: Union[str, None] = "ffa2cd90434a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "identity_profiles",
        sa.Column("arsenal_voice_settings", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("identity_profiles", "arsenal_voice_settings")
