"""create assignments table

Revision ID: l2a3b4c5d6e7
Revises: k1f2a3b4c5d6
Create Date: 2024-03-20 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l2a3b4c5d6e7'
down_revision: Union[str, Sequence[str], None] = 'k1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('assignment_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=False),
        sa.Column('terminal_id', sa.UUID(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('assignment_id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sales_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['terminal_id'], ['terminals.terminal_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.CheckConstraint("role IN ('cashier', 'supervisor')", name='ck_assignments_role')
    )
    
    # Create indexes
    op.create_index('idx_assignments_session', 'assignments', ['session_id'])
    op.create_index('idx_assignments_user', 'assignments', ['user_id'])
    op.create_index('idx_assignments_branch', 'assignments', ['branch_id'])
    op.create_index('idx_assignments_active', 'assignments', ['session_id', 'is_active'])
    
    # Create partial unique index to enforce single active assignment per user
    op.create_index(
        'idx_assignments_user_active_unique',
        'assignments',
        ['user_id', 'is_active'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('idx_assignments_user_active_unique', table_name='assignments')
    op.drop_index('idx_assignments_active', table_name='assignments')
    op.drop_index('idx_assignments_branch', table_name='assignments')
    op.drop_index('idx_assignments_user', table_name='assignments')
    op.drop_index('idx_assignments_session', table_name='assignments')
    
    # Drop table
    op.drop_table('assignments')
