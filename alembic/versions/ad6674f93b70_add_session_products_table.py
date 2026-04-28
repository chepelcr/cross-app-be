"""add_session_products_table

Revision ID: ad6674f93b70
Revises: facc4b47c490
Create Date: 2026-04-28 10:35:27.139035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad6674f93b70'
down_revision: Union[str, Sequence[str], None] = 'facc4b47c490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create session_products table
    op.create_table(
        'session_products',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('product_id', sa.String(length=255), nullable=False),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['sales_sessions.session_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id', 'product_id', name='uq_session_product')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_session_products_session', 'session_products', ['session_id'])
    op.create_index('idx_session_products_product', 'session_products', ['product_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_session_products_product', table_name='session_products')
    op.drop_index('idx_session_products_session', table_name='session_products')
    
    # Drop table
    op.drop_table('session_products')
