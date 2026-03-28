"""remove identification_type from clients

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8c9d0e1f2a3'
down_revision = 'g7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('clients', 'identification_type')


def downgrade() -> None:
    op.add_column('clients', sa.Column('identification_type', sa.Integer(), nullable=True))
