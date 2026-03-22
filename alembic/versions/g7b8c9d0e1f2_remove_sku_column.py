"""remove sku column

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-06 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g7b8c9d0e1f2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove SKU column from products table.
    
    SKU is now handled as code type 03 (MANUFACTURER) in the codes JSONB array.
    Before dropping, migrate any existing SKU values to the codes array.
    """
    # Migrate existing SKU values to codes array as type 03 (MANUFACTURER)
    op.execute("""
        UPDATE products 
        SET codes = CASE 
            WHEN sku IS NOT NULL AND sku != '' THEN 
                COALESCE(codes, '[]'::jsonb) || jsonb_build_array(
                    jsonb_build_object('codeTypeId', '03', 'number', sku)
                )
            ELSE codes
        END
        WHERE sku IS NOT NULL AND sku != ''
    """)
    
    # Drop the SKU column
    op.drop_column('products', 'sku')


def downgrade() -> None:
    """
    Rollback: Add SKU column back and extract from codes array.
    """
    # Add SKU column back
    op.add_column('products', sa.Column('sku', sa.String(100), nullable=True))
    
    # Extract SKU from codes array (code type 03)
    op.execute("""
        UPDATE products 
        SET sku = (
            SELECT elem->>'number'
            FROM jsonb_array_elements(codes) AS elem
            WHERE elem->>'codeTypeId' = '03'
            LIMIT 1
        )
        WHERE codes IS NOT NULL
    """)
