"""Add better_stats_user_favorite table.

Revision ID: c3d4e5f6a7b8
Revises: b512650591d4
Create Date: 2026-04-11 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b512650591d4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "better_stats_user_favorite",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "metric_name", name="uq_bstats_user_favorite"),
    )
    op.create_index(
        "ix_better_stats_user_favorite_user_id",
        "better_stats_user_favorite",
        ["user_id"],
    )


def downgrade():
    op.drop_index(
        "ix_better_stats_user_favorite_user_id",
        table_name="better_stats_user_favorite",
    )
    op.drop_table("better_stats_user_favorite")
