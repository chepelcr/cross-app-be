"""add_neighborhood_id_to_clients

Revision ID: facc4b47c490
Revises: d1f2a3b4c5e6
Create Date: 2026-04-25 06:56:24.331368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'facc4b47c490'
down_revision: Union[str, Sequence[str], None] = 'd1f2a3b4c5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('clients', sa.Column('neighborhood_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('clients', 'neighborhood_id')
