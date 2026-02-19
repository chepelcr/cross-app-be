"""add_client_status

Revision ID: bcede4283772
Revises: 558dd90ee76b
Create Date: 2026-02-18 19:35:25.556106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bcede4283772'
down_revision: Union[str, Sequence[str], None] = '558dd90ee76b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if status column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('clients')]
    
    if 'status' not in columns:
        op.add_column('clients', sa.Column('status', sa.Integer(), nullable=False, server_default='0'))
        op.alter_column('clients', 'status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Check if status column exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('clients')]
    
    if 'status' in columns:
        op.drop_column('clients', 'status')
