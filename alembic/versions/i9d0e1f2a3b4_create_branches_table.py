"""create branches table

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2024-03-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i9d0e1f2a3b4'
down_revision: Union[str, Sequence[str], None] = 'h8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create trigger function for updating updated_at timestamp (if not exists)
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    # Create branches table
    op.create_table(
        'branches',
        sa.Column('branch_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('branch_id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("type IN ('stand', 'restaurant')", name='check_branch_type'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_branches_org_code')
    )
    
    # Create indexes
    op.create_index('idx_branches_org', 'branches', ['organization_id'])
    op.create_index('idx_branches_active', 'branches', ['organization_id', 'is_active'])
    
    # Create trigger for updated_at
    op.execute(sa.text("""
        CREATE TRIGGER update_branches_updated_at
        BEFORE UPDATE ON branches
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop trigger
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_branches_updated_at ON branches"))
    
    # Drop indexes
    op.drop_index('idx_branches_active', table_name='branches')
    op.drop_index('idx_branches_org', table_name='branches')
    
    # Drop table
    op.drop_table('branches')
    
    # Note: We don't drop the update_updated_at_column function as it may be used by other tables
