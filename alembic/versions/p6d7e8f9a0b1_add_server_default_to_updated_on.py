"""add server default to updated_on columns

Revision ID: p6d7e8f9a0b1
Revises: o5d6e7f8a9b0
Create Date: 2024-03-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'p6d7e8f9a0b1'
down_revision: Union[str, Sequence[str], None] = 'o5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add server default NOW() to updated_on columns to match TimestampMixin behavior."""
    
    # Add server default to branches.updated_on
    op.execute(sa.text("""
        ALTER TABLE branches 
        ALTER COLUMN updated_on SET DEFAULT NOW()
    """))
    
    # Add server default to terminals.updated_on
    op.execute(sa.text("""
        ALTER TABLE terminals 
        ALTER COLUMN updated_on SET DEFAULT NOW()
    """))
    
    # Add server default to sales_sessions.updated_on
    op.execute(sa.text("""
        ALTER TABLE sales_sessions 
        ALTER COLUMN updated_on SET DEFAULT NOW()
    """))
    
    # Add server default to assignments.updated_on
    op.execute(sa.text("""
        ALTER TABLE assignments 
        ALTER COLUMN updated_on SET DEFAULT NOW()
    """))
    
    # Add server default to closings.updated_on
    op.execute(sa.text("""
        ALTER TABLE closings 
        ALTER COLUMN updated_on SET DEFAULT NOW()
    """))


def downgrade() -> None:
    """Remove server default from updated_on columns."""
    
    # Remove server default from branches.updated_on
    op.execute(sa.text("""
        ALTER TABLE branches 
        ALTER COLUMN updated_on DROP DEFAULT
    """))
    
    # Remove server default from terminals.updated_on
    op.execute(sa.text("""
        ALTER TABLE terminals 
        ALTER COLUMN updated_on DROP DEFAULT
    """))
    
    # Remove server default from sales_sessions.updated_on
    op.execute(sa.text("""
        ALTER TABLE sales_sessions 
        ALTER COLUMN updated_on DROP DEFAULT
    """))
    
    # Remove server default from assignments.updated_on
    op.execute(sa.text("""
        ALTER TABLE assignments 
        ALTER COLUMN updated_on DROP DEFAULT
    """))
    
    # Remove server default from closings.updated_on
    op.execute(sa.text("""
        ALTER TABLE closings 
        ALTER COLUMN updated_on DROP DEFAULT
    """))
