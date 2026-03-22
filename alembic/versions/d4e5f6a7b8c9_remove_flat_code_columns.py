"""remove flat code columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2024-03-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrate flat code columns to JSONB codes array, then drop flat columns.
    
    This migration:
    1. Migrates existing flat column data to codes JSONB array
    2. Drops the flat code columns (internal_code, original_code, client_article_code, code)
    3. Drops the unique index on internal_code
    """
    
    # Step 1: Migrate existing flat column data to codes array
    # Build codes array from flat columns for products that don't have codes yet
    op.execute("""
        UPDATE products
        SET codes = (
            SELECT jsonb_agg(code_obj)
            FROM (
                SELECT jsonb_build_object(
                    'codeTypeId', '04',
                    'number', internal_code
                ) AS code_obj
                WHERE internal_code IS NOT NULL
                
                UNION ALL
                
                SELECT jsonb_build_object(
                    'codeTypeId', '01',
                    'number', original_code
                ) AS code_obj
                WHERE original_code IS NOT NULL
                
                UNION ALL
                
                SELECT jsonb_build_object(
                    'codeTypeId', '02',
                    'number', client_article_code
                ) AS code_obj
                WHERE client_article_code IS NOT NULL
                
                UNION ALL
                
                SELECT jsonb_build_object(
                    'codeTypeId', '03',
                    'number', code
                ) AS code_obj
                WHERE code IS NOT NULL
            ) AS codes_data
        )
        WHERE (codes IS NULL OR codes = '[]'::jsonb)
        AND (internal_code IS NOT NULL OR original_code IS NOT NULL 
             OR client_article_code IS NOT NULL OR code IS NOT NULL)
    """)
    
    # Step 2: Drop the unique index on internal_code
    op.drop_index('idx_product_org_internal_code', table_name='products')
    
    # Step 3: Drop the flat code columns
    op.drop_column('products', 'internal_code')
    op.drop_column('products', 'original_code')
    op.drop_column('products', 'client_article_code')
    op.drop_column('products', 'code')


def downgrade():
    """
    Restore flat code columns from JSONB codes array.
    
    This is a lossy downgrade - only the first code of each type will be restored.
    """
    
    # Step 1: Re-add the flat code columns
    op.add_column('products', sa.Column('internal_code', sa.String(50), nullable=True))
    op.add_column('products', sa.Column('original_code', sa.String(50), nullable=True))
    op.add_column('products', sa.Column('client_article_code', sa.String(50), nullable=True))
    op.add_column('products', sa.Column('code', sa.String(50), nullable=True))
    
    # Step 2: Restore data from codes array (first code of each type)
    op.execute("""
        UPDATE products
        SET 
            internal_code = (
                SELECT elem->>'number'
                FROM jsonb_array_elements(codes) AS elem
                WHERE elem->>'codeTypeId' = '04'
                LIMIT 1
            ),
            original_code = (
                SELECT elem->>'number'
                FROM jsonb_array_elements(codes) AS elem
                WHERE elem->>'codeTypeId' = '01'
                LIMIT 1
            ),
            client_article_code = (
                SELECT elem->>'number'
                FROM jsonb_array_elements(codes) AS elem
                WHERE elem->>'codeTypeId' = '02'
                LIMIT 1
            ),
            code = (
                SELECT elem->>'number'
                FROM jsonb_array_elements(codes) AS elem
                WHERE elem->>'codeTypeId' = '03'
                LIMIT 1
            )
        WHERE codes IS NOT NULL AND codes != '[]'::jsonb
    """)
    
    # Step 3: Re-create the unique index
    op.create_index('idx_product_org_internal_code', 'products', 
                    ['organization_id', 'internal_code'], unique=True)
