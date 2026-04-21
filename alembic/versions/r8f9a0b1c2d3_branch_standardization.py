"""branch standardization: replace is_active with status, add consecutives table

Revision ID: r8f9a0b1c2d3
Revises: q7e8f9a0b1c2
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'q7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace is_active with status on branches and terminals, create consecutives."""
    # --- branches ---
    op.add_column('branches', sa.Column('status', sa.Integer(), nullable=False, server_default='1'))
    op.execute(sa.text("UPDATE branches SET status = CASE WHEN is_active THEN 1 ELSE 2 END"))
    op.drop_index('idx_branches_active', table_name='branches')
    op.drop_column('branches', 'is_active')
    op.create_index('idx_branches_status', 'branches', ['organization_id', 'status'])

    # --- terminals ---
    op.add_column('terminals', sa.Column('status', sa.Integer(), nullable=False, server_default='1'))
    op.execute(sa.text("UPDATE terminals SET status = CASE WHEN is_active THEN 1 ELSE 2 END"))
    op.drop_index('idx_terminals_active', table_name='terminals')
    op.drop_column('terminals', 'is_active')
    op.create_index('idx_terminals_status', 'terminals', ['organization_id', 'status'])

    # --- consecutives ---
    op.create_table(
        'consecutives',
        sa.Column('consecutive_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('terminal_id', sa.UUID(), nullable=False),
        sa.Column('document_type_id', sa.Integer(), nullable=False),
        sa.Column('current_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.Column('deleted_on', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['terminal_id'], ['terminals.terminal_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_type_id'], ['document_types.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('consecutive_id'),
        sa.UniqueConstraint('terminal_id', 'document_type_id', name='uq_consecutives_terminal_doc_type'),
    )
    op.create_index('idx_consecutives_org', 'consecutives', ['organization_id'])
    op.create_index('idx_consecutives_terminal', 'consecutives', ['terminal_id'])


def downgrade() -> None:
    """Reverse migration."""
    # --- consecutives ---
    op.drop_index('idx_consecutives_terminal', table_name='consecutives')
    op.drop_index('idx_consecutives_org', table_name='consecutives')
    op.drop_table('consecutives')

    # --- terminals ---
    op.drop_index('idx_terminals_status', table_name='terminals')
    op.add_column('terminals', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.execute(sa.text("UPDATE terminals SET is_active = CASE WHEN status = 1 THEN true ELSE false END"))
    op.drop_column('terminals', 'status')
    op.create_index('idx_terminals_active', 'terminals', ['organization_id', 'is_active'])

    # --- branches ---
    op.drop_index('idx_branches_status', table_name='branches')
    op.add_column('branches', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.execute(sa.text("UPDATE branches SET is_active = CASE WHEN status = 1 THEN true ELSE false END"))
    op.drop_column('branches', 'status')
    op.create_index('idx_branches_active', 'branches', ['organization_id', 'is_active'])
