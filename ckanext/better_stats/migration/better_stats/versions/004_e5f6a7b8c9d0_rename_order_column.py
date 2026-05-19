"""Rename better_stats_metric_config.order column to display_order.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-17 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "better_stats_metric_config",
        "order",
        new_column_name="display_order",
    )


def downgrade():
    op.alter_column(
        "better_stats_metric_config",
        "display_order",
        new_column_name="order",
    )
