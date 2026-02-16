"""add_crossdocking_pdf_and_store_slots

Revision ID: a1b2c3d4e5f6
Revises: 49d382b10383
Create Date: 2026-02-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '49d382b10383'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New columns on crossdocking_orders
    op.add_column('crossdocking_orders', sa.Column('crossdocking_pdf_url', sa.String(length=500), nullable=True))
    op.add_column('crossdocking_orders', sa.Column('nuevo_reporte_url', sa.String(length=500), nullable=True))

    # New column on crossdocking_sale_points
    op.add_column('crossdocking_sale_points', sa.Column('slot_id', sa.String(length=20), nullable=True))

    # New store_slots reference table
    op.create_table(
        'store_slots',
        sa.Column('store_code', sa.String(length=20), nullable=False),
        sa.Column('store_name', sa.String(length=200), nullable=True),
        sa.Column('slot_id', sa.String(length=20), nullable=True),
        sa.Column('chain', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('store_code'),
    )


def downgrade() -> None:
    op.drop_table('store_slots')
    op.drop_column('crossdocking_sale_points', 'slot_id')
    op.drop_column('crossdocking_orders', 'nuevo_reporte_url')
    op.drop_column('crossdocking_orders', 'crossdocking_pdf_url')
