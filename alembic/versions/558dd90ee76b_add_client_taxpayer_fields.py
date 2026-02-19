"""add_client_taxpayer_fields

Revision ID: 558dd90ee76b
Revises: fb21eb6dec2c
Create Date: 2026-02-18 19:19:28.163130

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '558dd90ee76b'
down_revision: Union[str, Sequence[str], None] = 'fb21eb6dec2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add identification fields
    op.add_column('clients', sa.Column('identification_type', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('identification_code', sa.String(length=10), nullable=True))
    op.add_column('clients', sa.Column('identification_number', sa.String(length=50), nullable=True))
    
    # Add business info fields
    op.add_column('clients', sa.Column('business_name', sa.String(length=255), nullable=True))
    op.add_column('clients', sa.Column('nationality', sa.String(length=3), nullable=True))
    op.add_column('clients', sa.Column('email', sa.String(length=255), nullable=True))
    
    # Add phone fields
    op.add_column('clients', sa.Column('phone_country_code', sa.String(length=10), nullable=True))
    op.add_column('clients', sa.Column('phone_area_code', sa.String(length=10), nullable=True))
    op.add_column('clients', sa.Column('phone_number', sa.String(length=20), nullable=True))
    op.add_column('clients', sa.Column('phone_description', sa.String(length=50), nullable=True))
    
    # Add residence fields
    op.add_column('clients', sa.Column('state_id', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('county_id', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('district_id', sa.Integer(), nullable=True))
    op.add_column('clients', sa.Column('address', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove residence fields
    op.drop_column('clients', 'address')
    op.drop_column('clients', 'district_id')
    op.drop_column('clients', 'county_id')
    op.drop_column('clients', 'state_id')
    
    # Remove phone fields
    op.drop_column('clients', 'phone_description')
    op.drop_column('clients', 'phone_number')
    op.drop_column('clients', 'phone_area_code')
    op.drop_column('clients', 'phone_country_code')
    
    # Remove business info fields
    op.drop_column('clients', 'email')
    op.drop_column('clients', 'nationality')
    op.drop_column('clients', 'business_name')
    
    # Remove identification fields
    op.drop_column('clients', 'identification_number')
    op.drop_column('clients', 'identification_code')
    op.drop_column('clients', 'identification_type')
