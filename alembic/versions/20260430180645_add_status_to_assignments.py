"""add status to assignments

Revision ID: 20260430180645
Revises: ad6674f93b70
Create Date: 2026-04-30 18:06:45

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260430180645'
down_revision = 'ad6674f93b70'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column with default value 1 (Active)
    op.add_column('assignments', sa.Column('status', sa.Integer(), nullable=False, server_default='1'))
    
    # Migrate existing data: set status based on is_active
    # is_active=True -> status=1 (Active)
    # is_active=False -> status=2 (Inactive)
    op.execute("""
        UPDATE assignments 
        SET status = CASE 
            WHEN is_active = true THEN 1 
            ELSE 2 
        END
    """)
    
    # Create new index for status
    op.create_index('idx_assignments_status', 'assignments', ['session_id', 'status'])
    
    # Drop old unique index for is_active
    op.drop_index('idx_user_active_assignment', table_name='assignments', postgresql_where=sa.text('is_active = true'))
    
    # Create new unique index for status
    op.create_index(
        'idx_user_active_assignment', 
        'assignments', 
        ['user_id', 'status'], 
        unique=True,
        postgresql_where=sa.text('status = 1')
    )
    
    # Drop is_active column
    op.drop_column('assignments', 'is_active')
    
    # Drop old index
    op.drop_index('idx_assignments_active', table_name='assignments')


def downgrade():
    # Add back is_active column
    op.add_column('assignments', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Migrate data back: status=1 -> is_active=true, otherwise false
    op.execute("""
        UPDATE assignments 
        SET is_active = CASE 
            WHEN status = 1 THEN true 
            ELSE false 
        END
    """)
    
    # Recreate old indexes
    op.create_index('idx_assignments_active', 'assignments', ['session_id', 'is_active'])
    
    # Drop new unique index
    op.drop_index('idx_user_active_assignment', table_name='assignments', postgresql_where=sa.text('status = 1'))
    
    # Recreate old unique index
    op.create_index(
        'idx_user_active_assignment', 
        'assignments', 
        ['user_id', 'is_active'], 
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )
    
    # Drop status column and index
    op.drop_index('idx_assignments_status', table_name='assignments')
    op.drop_column('assignments', 'status')
