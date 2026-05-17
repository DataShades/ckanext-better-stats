"""Add better_stats_metric_config table.

Revision ID: b512650591d4
Revises:
Create Date: 2026-04-04 16:23:55.205086
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b512650591d4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "better_stats_metric_config",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("order", sa.Integer(), nullable=True, server_default="100"),
        sa.Column("col_span", sa.SmallInteger(), nullable=True, server_default="3"),
        sa.Column("row_span", sa.SmallInteger(), nullable=True, server_default="1"),
        sa.Column("access_level", sa.String(20), nullable=True),
        sa.Column("cache_timeout", sa.Integer(), nullable=True, server_default="3600"),
        sa.Column(
            "extras",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("modified", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_name"),
    )
    op.create_index(
        "ix_better_stats_metric_config_metric_name",
        "better_stats_metric_config",
        ["metric_name"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        "ix_better_stats_metric_config_metric_name",
        table_name="better_stats_metric_config",
    )
    op.drop_table("better_stats_metric_config")
