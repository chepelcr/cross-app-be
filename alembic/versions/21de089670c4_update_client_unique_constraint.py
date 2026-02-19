"""update_client_unique_constraint

Revision ID: 21de089670c4
Revises: bcede4283772
Create Date: 2026-02-18 19:38:13.445881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21de089670c4'
down_revision: Union[str, Sequence[str], None] = 'bcede4283772'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('clients')]
    
    # Drop old index if exists
    if 'idx_client_company_gln' in indexes:
        op.drop_index('idx_client_company_gln', table_name='clients')
    
    # Create new index if not exists
    if 'idx_client_company_gln_nationality' not in indexes:
        op.create_index('idx_client_company_gln_nationality', 'clients', ['company_id', 'client_gln', 'nationality'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('clients')]
    
    # Drop new index if exists
    if 'idx_client_company_gln_nationality' in indexes:
        op.drop_index('idx_client_company_gln_nationality', table_name='clients')
    
    # Recreate old index if not exists
    if 'idx_client_company_gln' not in indexes:
        op.create_index('idx_client_company_gln', 'clients', ['company_id', 'client_gln'], unique=True)
