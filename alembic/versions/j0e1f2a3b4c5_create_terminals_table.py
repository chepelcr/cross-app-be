"""create terminals table

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2024-03-20 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j0e1f2a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'i9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create terminals table
    op.create_table(
        'terminals',
        sa.Column('terminal_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('registered_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_seen_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('terminal_id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.branch_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_terminals_org_code'),
        sa.UniqueConstraint('device_id', name='uq_terminals_device_id')
    )
    
    # Create indexes
    op.create_index('idx_terminals_branch', 'terminals', ['branch_id'])
    op.create_index('idx_terminals_org', 'terminals', ['organization_id'])
    op.create_index('idx_terminals_active', 'terminals', ['organization_id', 'is_active'])
    
    # Create trigger for updated_at
    op.execute(sa.text("""
        CREATE TRIGGER update_terminals_updated_at
        BEFORE UPDATE ON terminals
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_terminals_updated_at ON terminals"))
    
    # Drop indexes
    op.drop_index('idx_terminals_active', table_name='terminals')
    op.drop_index('idx_terminals_org', table_name='terminals')
    op.drop_index('idx_terminals_branch', table_name='terminals')
    
    # Drop table
    op.drop_table('terminals')
