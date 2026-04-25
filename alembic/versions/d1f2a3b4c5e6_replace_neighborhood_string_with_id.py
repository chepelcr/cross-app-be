"""replace_neighborhood_string_with_neighborhood_id

Revision ID: d1f2a3b4c5e6
Revises: c26559cef2c5
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd1f2a3b4c5e6'
down_revision: Union[str, Sequence[str], None] = 'c26559cef2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace neighborhood varchar with neighborhood_id integer."""
    op.drop_column('branches', 'neighborhood')
    op.add_column('branches', sa.Column('neighborhood_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Revert neighborhood_id integer back to neighborhood varchar."""
    op.drop_column('branches', 'neighborhood_id')
    op.add_column('branches', sa.Column('neighborhood', sa.String(length=255), nullable=True))
