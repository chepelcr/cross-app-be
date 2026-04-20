"""increase varchar lengths for organization_id and user_id fields

Revision ID: o5d6e7f8a9b0
Revises: n4c5d6e7f8a9
Create Date: 2024-03-20 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'o5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'n4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase VARCHAR lengths for organization_id and user_id fields to accommodate test data."""
    
    # Branches table
    op.alter_column('branches', 'organization_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('branches', 'created_by',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Terminals table
    op.alter_column('terminals', 'organization_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Sessions table
    op.alter_column('sales_sessions', 'organization_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('sales_sessions', 'created_by',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Assignments table
    op.alter_column('assignments', 'organization_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('assignments', 'user_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('assignments', 'created_by',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    
    # Closings table
    op.alter_column('closings', 'organization_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('closings', 'cashier_id',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=False)
    op.alter_column('closings', 'reviewed_by',
                    existing_type=sa.String(length=36),
                    type_=sa.String(length=255),
                    existing_nullable=True)


def downgrade() -> None:
    """Revert VARCHAR lengths back to 36."""
    
    # Closings table
    op.alter_column('closings', 'reviewed_by',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=True)
    op.alter_column('closings', 'cashier_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    op.alter_column('closings', 'organization_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    
    # Assignments table
    op.alter_column('assignments', 'created_by',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    op.alter_column('assignments', 'user_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    op.alter_column('assignments', 'organization_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    
    # Sessions table
    op.alter_column('sales_sessions', 'created_by',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    op.alter_column('sales_sessions', 'organization_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    
    # Terminals table
    op.alter_column('terminals', 'organization_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    
    # Branches table
    op.alter_column('branches', 'created_by',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
    op.alter_column('branches', 'organization_id',
                    existing_type=sa.String(length=255),
                    type_=sa.String(length=36),
                    existing_nullable=False)
