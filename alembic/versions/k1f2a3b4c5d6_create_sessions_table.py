"""create sessions table

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2024-03-20 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = 'j0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create sales_sessions table
    op.create_table(
        'sales_sessions',
        sa.Column('session_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('context', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('expected_revenue', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('actual_revenue', sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('session_id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.CheckConstraint("type IN ('match', 'shift')", name='ck_sessions_type'),
        sa.CheckConstraint("context IN ('gradas', 'mesa', 'caja')", name='ck_sessions_context')
    )
    
    # Create indexes
    op.create_index('idx_sales_sessions_org', 'sales_sessions', ['organization_id'])
    op.create_index('idx_sales_sessions_active', 'sales_sessions', ['organization_id', 'is_active'])
    op.create_index('idx_sales_sessions_branch', 'sales_sessions', ['branch_id'])
    op.create_index('idx_sales_sessions_time', 'sales_sessions', [sa.text('start_time DESC')])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_sales_sessions_time', table_name='sales_sessions')
    op.drop_index('idx_sales_sessions_branch', table_name='sales_sessions')
    op.drop_index('idx_sales_sessions_active', table_name='sales_sessions')
    op.drop_index('idx_sales_sessions_org', table_name='sales_sessions')
    
    # Drop table
    op.drop_table('sales_sessions')
