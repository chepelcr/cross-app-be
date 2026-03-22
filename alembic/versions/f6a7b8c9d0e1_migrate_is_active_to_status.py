"""migrate is_active to status

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Migrate from is_active (boolean) to status (integer).
    
    Migration steps:
    1. Add new status column (nullable initially)
    2. Migrate data: is_active=true -> status=1, is_active=false -> status=2
    3. Make status NOT NULL with default value
    4. Drop is_active column
    """
    # Step 1: Add status column (nullable)
    op.add_column('products', sa.Column('status', sa.Integer(), nullable=True))
    
    # Step 2: Migrate existing data
    # Convert is_active=true to status=1 (ACTIVE)
    # Convert is_active=false to status=2 (INACTIVE)
    op.execute("""
        UPDATE products 
        SET status = CASE 
            WHEN is_active = true THEN 1 
            WHEN is_active = false THEN 2 
            ELSE 1 
        END
    """)
    
    # Step 3: Make status NOT NULL with default
    op.alter_column('products', 'status',
                    existing_type=sa.Integer(),
                    nullable=False,
                    server_default='1')
    
    # Step 4: Drop is_active column
    op.drop_column('products', 'is_active')
    
    # Add index on status for better query performance
    op.create_index('ix_products_status', 'products', ['status'])


def downgrade() -> None:
    """
    Rollback migration: status (integer) back to is_active (boolean).
    """
    # Drop status index
    op.drop_index('ix_products_status', table_name='products')
    
    # Add back is_active column
    op.add_column('products', sa.Column('is_active', sa.Boolean(), nullable=True))
    
    # Migrate data back: status=1 -> is_active=true, status=2,3 -> is_active=false
    op.execute("""
        UPDATE products 
        SET is_active = CASE 
            WHEN status = 1 THEN true 
            ELSE false 
        END
    """)
    
    # Make is_active NOT NULL
    op.alter_column('products', 'is_active',
                    existing_type=sa.Boolean(),
                    nullable=False,
                    server_default='true')
    
    # Drop status column
    op.drop_column('products', 'status')
