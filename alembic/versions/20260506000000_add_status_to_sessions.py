"""add status to sessions

Revision ID: 20260506000000
Revises: 20260430180645
Create Date: 2026-05-06 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260506000000'
down_revision = '20260430180645'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column with default value 1 (Active)
    op.add_column('sales_sessions', sa.Column('status', sa.Integer(), nullable=False, server_default='1'))

    # Migrate existing data: set status based on is_active
    # is_active=True -> status=1 (Active)
    # is_active=False -> status=2 (Inactive)
    op.execute("""
        UPDATE sales_sessions
        SET status = CASE
            WHEN is_active = true THEN 1
            ELSE 2
        END
    """)

    # Create new index for status
    op.create_index('idx_sessions_status', 'sales_sessions', ['organization_id', 'status'])

    # Drop old index on is_active
    op.execute("""
        DROP INDEX IF EXISTS idx_sessions_active;
    """)

    # Drop is_active column
    op.drop_column('sales_sessions', 'is_active')


def downgrade():
    # Add back is_active column
    op.add_column('sales_sessions', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    # Migrate data back: status=1 -> is_active=true, otherwise false
    op.execute("""
        UPDATE sales_sessions
        SET is_active = CASE
            WHEN status = 1 THEN true
            ELSE false
        END
    """)

    # Recreate old index
    op.create_index('idx_sessions_active', 'sales_sessions', ['organization_id', 'is_active'])

    # Drop new status index and column
    op.drop_index('idx_sessions_status', table_name='sales_sessions')
    op.drop_column('sales_sessions', 'status')
