"""make updated_on nullable to match TimestampMixin

Revision ID: q7e8f9a0b1c2
Revises: p6d7e8f9a0b1
Create Date: 2024-03-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'q7e8f9a0b1c2'
down_revision: Union[str, Sequence[str], None] = 'p6d7e8f9a0b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Make updated_on columns nullable to match TimestampMixin (nullable=True)."""
    
    # Make branches.updated_on nullable
    op.execute(sa.text("""
        ALTER TABLE branches 
        ALTER COLUMN updated_on DROP NOT NULL
    """))
    
    # Make terminals.updated_on nullable
    op.execute(sa.text("""
        ALTER TABLE terminals 
        ALTER COLUMN updated_on DROP NOT NULL
    """))
    
    # Make sales_sessions.updated_on nullable
    op.execute(sa.text("""
        ALTER TABLE sales_sessions 
        ALTER COLUMN updated_on DROP NOT NULL
    """))
    
    # Make assignments.updated_on nullable
    op.execute(sa.text("""
        ALTER TABLE assignments 
        ALTER COLUMN updated_on DROP NOT NULL
    """))
    
    # Make closings.updated_on nullable
    op.execute(sa.text("""
        ALTER TABLE closings 
        ALTER COLUMN updated_on DROP NOT NULL
    """))


def downgrade() -> None:
    """Make updated_on columns NOT NULL again."""
    
    # Make branches.updated_on NOT NULL
    op.execute(sa.text("""
        ALTER TABLE branches 
        ALTER COLUMN updated_on SET NOT NULL
    """))
    
    # Make terminals.updated_on NOT NULL
    op.execute(sa.text("""
        ALTER TABLE terminals 
        ALTER COLUMN updated_on SET NOT NULL
    """))
    
    # Make sales_sessions.updated_on NOT NULL
    op.execute(sa.text("""
        ALTER TABLE sales_sessions 
        ALTER COLUMN updated_on SET NOT NULL
    """))
    
    # Make assignments.updated_on NOT NULL
    op.execute(sa.text("""
        ALTER TABLE assignments 
        ALTER COLUMN updated_on SET NOT NULL
    """))
    
    # Make closings.updated_on NOT NULL
    op.execute(sa.text("""
        ALTER TABLE closings 
        ALTER COLUMN updated_on SET NOT NULL
    """))
