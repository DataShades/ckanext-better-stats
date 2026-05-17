"""Make better_stats datetime columns timezone-aware.

Existing rows are naive UTC (written from a tz-aware datetime that Postgres
stripped on insert), so reinterpret them at UTC during the type change.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-17 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "better_stats_metric_config",
        "created",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="created AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "better_stats_metric_config",
        "modified",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="modified AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "better_stats_user_favorite",
        "created",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True,
        postgresql_using="created AT TIME ZONE 'UTC'",
    )


def downgrade():
    op.alter_column(
        "better_stats_user_favorite",
        "created",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="created AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "better_stats_metric_config",
        "modified",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="modified AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        "better_stats_metric_config",
        "created",
        type_=sa.DateTime(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using="created AT TIME ZONE 'UTC'",
    )
