"""Allow the complete ten-digit Hacienda serial in consecutive counters.

Revision ID: be1f2a3b4c5d
Revises: bd0e1f2a3b4c
Create Date: 2026-09-11
"""

import sqlalchemy as sa
from alembic import op

revision = "be1f2a3b4c5d"
down_revision = "bd0e1f2a3b4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "consecutives", "current_number",
        existing_type=sa.Integer(), type_=sa.BigInteger(), existing_nullable=False,
    )


def downgrade() -> None:
    # PostgreSQL refuses the narrowing conversion if any counter no longer fits.
    # Never truncate or reset a fiscal sequence to make a downgrade succeed.
    op.alter_column(
        "consecutives", "current_number",
        existing_type=sa.BigInteger(), type_=sa.Integer(), existing_nullable=False,
    )
