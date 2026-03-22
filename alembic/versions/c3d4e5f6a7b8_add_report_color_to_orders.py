"""Add report_color column to crossdocking_orders.

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-03-03

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "crossdocking_orders",
        sa.Column("report_color", sa.String(20), nullable=True, server_default="green"),
    )


def downgrade() -> None:
    op.drop_column("crossdocking_orders", "report_color")
