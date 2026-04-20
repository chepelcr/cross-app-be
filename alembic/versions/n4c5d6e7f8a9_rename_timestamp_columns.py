"""rename timestamp columns to match TimestampMixin convention

Revision ID: n4c5d6e7f8a9
Revises: m3b4c5d6e7f8
Create Date: 2024-03-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'n4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'm3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename timestamp columns to match TimestampMixin convention (created_on, updated_on)."""
    
    # Branches table
    op.alter_column('branches', 'created_at', new_column_name='created_on')
    op.alter_column('branches', 'updated_at', new_column_name='updated_on')
    
    # Add deleted_on column to branches
    op.add_column('branches', sa.Column('deleted_on', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Terminals table
    op.alter_column('terminals', 'created_at', new_column_name='created_on')
    op.alter_column('terminals', 'updated_at', new_column_name='updated_on')
    
    # Add deleted_on column to terminals
    op.add_column('terminals', sa.Column('deleted_on', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Update triggers to use new column names
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS update_branches_updated_at ON branches;
        
        CREATE TRIGGER update_branches_updated_on
        BEFORE UPDATE ON branches
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS update_terminals_updated_at ON terminals;
        
        CREATE TRIGGER update_terminals_updated_on
        BEFORE UPDATE ON terminals
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    # Update the trigger function to use updated_on instead of updated_at
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_on = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    # Sessions table (sales_sessions)
    op.alter_column('sales_sessions', 'created_at', new_column_name='created_on')
    
    # Add updated_on and deleted_on columns to sales_sessions
    op.add_column('sales_sessions', sa.Column('updated_on', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('sales_sessions', sa.Column('deleted_on', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Add trigger for sales_sessions
    op.execute(sa.text("""
        CREATE TRIGGER update_sales_sessions_updated_on
        BEFORE UPDATE ON sales_sessions
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    # Assignments table
    op.alter_column('assignments', 'created_at', new_column_name='created_on')
    
    # Add updated_on and deleted_on columns to assignments
    op.add_column('assignments', sa.Column('updated_on', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('assignments', sa.Column('deleted_on', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Add trigger for assignments
    op.execute(sa.text("""
        CREATE TRIGGER update_assignments_updated_on
        BEFORE UPDATE ON assignments
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    # Closings table
    op.alter_column('closings', 'created_at', new_column_name='created_on')
    
    # Add updated_on and deleted_on columns to closings
    op.add_column('closings', sa.Column('updated_on', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('closings', sa.Column('deleted_on', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Add trigger for closings
    op.execute(sa.text("""
        CREATE TRIGGER update_closings_updated_on
        BEFORE UPDATE ON closings
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))


def downgrade() -> None:
    """Revert timestamp columns back to created_at/updated_at convention."""
    
    # Drop triggers
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_branches_updated_on ON branches"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_terminals_updated_on ON terminals"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_sales_sessions_updated_on ON sales_sessions"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_assignments_updated_on ON assignments"))
    op.execute(sa.text("DROP TRIGGER IF EXISTS update_closings_updated_on ON closings"))
    
    # Branches table
    op.drop_column('branches', 'deleted_on')
    op.alter_column('branches', 'created_on', new_column_name='created_at')
    op.alter_column('branches', 'updated_on', new_column_name='updated_at')
    
    # Terminals table
    op.drop_column('terminals', 'deleted_on')
    op.alter_column('terminals', 'created_on', new_column_name='created_at')
    op.alter_column('terminals', 'updated_on', new_column_name='updated_at')
    
    # Sessions table
    op.drop_column('sales_sessions', 'updated_on')
    op.drop_column('sales_sessions', 'deleted_on')
    op.alter_column('sales_sessions', 'created_on', new_column_name='created_at')
    
    # Assignments table
    op.drop_column('assignments', 'updated_on')
    op.drop_column('assignments', 'deleted_on')
    op.alter_column('assignments', 'created_on', new_column_name='created_at')
    
    # Closings table
    op.drop_column('closings', 'updated_on')
    op.drop_column('closings', 'deleted_on')
    op.alter_column('closings', 'created_on', new_column_name='created_at')
    
    # Recreate original triggers
    op.execute(sa.text("""
        CREATE TRIGGER update_branches_updated_at
        BEFORE UPDATE ON branches
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    op.execute(sa.text("""
        CREATE TRIGGER update_terminals_updated_at
        BEFORE UPDATE ON terminals
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """))
    
    # Restore original trigger function
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))
