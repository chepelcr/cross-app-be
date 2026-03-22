"""add timestamps to products

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2024-03-04 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    """Add timestamp columns to products table."""
    
    # Add timestamp columns
    op.add_column('products', sa.Column('created_on', sa.DateTime(), nullable=True))
    op.add_column('products', sa.Column('updated_on', sa.DateTime(), nullable=True))
    op.add_column('products', sa.Column('deleted_on', sa.DateTime(), nullable=True))
    
    # Set created_on to current timestamp for existing records
    op.execute(text("UPDATE products SET created_on = NOW() WHERE created_on IS NULL"))


def downgrade():
    """Remove timestamp columns from products table."""
    
    op.drop_column('products', 'deleted_on')
    op.drop_column('products', 'updated_on')
    op.drop_column('products', 'created_on')
