"""migrate_branch_address_to_location_structure

Revision ID: c26559cef2c5
Revises: r8f9a0b1c2d3
Create Date: 2026-04-21 13:16:13.789261

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c26559cef2c5'
down_revision: Union[str, Sequence[str], None] = 'r8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate branch address to structured location fields."""
    # Add new location columns
    op.add_column('branches', sa.Column('state_id', sa.Integer(), nullable=True))
    op.add_column('branches', sa.Column('county_id', sa.Integer(), nullable=True))
    op.add_column('branches', sa.Column('district_id', sa.Integer(), nullable=True))
    op.add_column('branches', sa.Column('neighborhood', sa.String(length=255), nullable=True))
    
    # Change address column type from String(500) to Text
    op.alter_column('branches', 'address',
                    existing_type=sa.String(length=500),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    """Revert branch location structure to simple address."""
    # Remove new location columns
    op.drop_column('branches', 'neighborhood')
    op.drop_column('branches', 'district_id')
    op.drop_column('branches', 'county_id')
    op.drop_column('branches', 'state_id')
    
    # Revert address column type back to String(500)
    op.alter_column('branches', 'address',
                    existing_type=sa.Text(),
                    type_=sa.String(length=500),
                    existing_nullable=True)
