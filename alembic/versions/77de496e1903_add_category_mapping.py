"""add_category_mapping

Revision ID: 77de496e1903
Revises: 7deff17aef26
Create Date: 2026-02-16 14:06:24.067265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77de496e1903'
down_revision: Union[str, Sequence[str], None] = '7deff17aef26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add image columns to categories table (shared with BeautyMarket).
    # FKs on products (organization_id, category_id) already exist from BeautyMarket.
    op.add_column('categories', sa.Column('image_1_url', sa.Text(), nullable=True))
    op.add_column('categories', sa.Column('image_2_url', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('categories', 'image_2_url')
    op.drop_column('categories', 'image_1_url')
