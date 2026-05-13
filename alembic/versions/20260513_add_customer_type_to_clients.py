"""add customer_type to clients

Revision ID: add_customer_type_to_clients
Revises: t0b1c2d3e4f5
Create Date: 2026-05-13 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_customer_type_to_clients'
down_revision: Union[str, None] = 't0b1c2d3e4f5'  # Previous revision: create_sales_tables
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add customer_type column to clients table
    op.add_column('clients', sa.Column('customer_type', sa.Integer(), nullable=True))
    
    # Create index for customer_type for faster filtering
    op.create_index('idx_client_customer_type', 'clients', ['customer_type'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_client_customer_type', table_name='clients')
    
    # Drop column
    op.drop_column('clients', 'customer_type')
