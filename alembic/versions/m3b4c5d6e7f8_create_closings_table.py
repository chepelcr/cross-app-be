"""create closings table

Revision ID: m3b4c5d6e7f8
Revises: l2a3b4c5d6e7
Create Date: 2024-03-20 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'l2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create closings table
    op.create_table(
        'closings',
        sa.Column('closing_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('assignment_id', sa.UUID(), nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=False),
        sa.Column('terminal_id', sa.UUID(), nullable=True),
        sa.Column('cashier_id', sa.String(length=36), nullable=False),
        
        # Expected amounts (from system)
        sa.Column('expected_cash', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('expected_sinpe', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('expected_card', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        sa.Column('expected_total', sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text('0')),
        
        # Declared amounts (from cashier)
        sa.Column('declared_cash', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('declared_sinpe', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('declared_card', sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column('declared_total', sa.DECIMAL(precision=12, scale=2), nullable=False),
        
        # Differences (calculated/generated columns)
        sa.Column('cash_difference', sa.DECIMAL(precision=12, scale=2), sa.Computed('(declared_cash - expected_cash)'), nullable=True),
        sa.Column('sinpe_difference', sa.DECIMAL(precision=12, scale=2), sa.Computed('(declared_sinpe - expected_sinpe)'), nullable=True),
        sa.Column('card_difference', sa.DECIMAL(precision=12, scale=2), sa.Computed('(declared_card - expected_card)'), nullable=True),
        sa.Column('total_difference', sa.DECIMAL(precision=12, scale=2), sa.Computed('(declared_total - expected_total)'), nullable=True),
        
        # Additional fields
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Primary key
        sa.PrimaryKeyConstraint('closing_id'),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sales_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.assignment_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['terminal_id'], ['terminals.terminal_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['cashier_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        
        # Check constraint for status
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='ck_closings_status')
    )
    
    # Create indexes
    op.create_index('idx_closings_session', 'closings', ['session_id'])
    op.create_index('idx_closings_status', 'closings', ['organization_id', 'status'])
    op.create_index('idx_closings_branch', 'closings', ['branch_id'])
    op.create_index('idx_closings_cashier', 'closings', ['cashier_id'])
    
    # Create unique constraint on assignment_id (one closing per assignment)
    op.create_unique_constraint('uq_closings_assignment', 'closings', ['assignment_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop unique constraint
    op.drop_constraint('uq_closings_assignment', 'closings', type_='unique')
    
    # Drop indexes
    op.drop_index('idx_closings_cashier', table_name='closings')
    op.drop_index('idx_closings_branch', table_name='closings')
    op.drop_index('idx_closings_status', table_name='closings')
    op.drop_index('idx_closings_session', table_name='closings')
    
    # Drop table
    op.drop_table('closings')
