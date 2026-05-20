"""replace products.unit_id with products.unit_measure (Hacienda code string)

Revision ID: replace_unit_id_w_measure
Revises: drop_legacy_cabys_name_type
Create Date: 2026-05-20

Context:
    `products.unit_id` was an Integer pointing at the data-services
    `measurement_units` catalog. Two problems:

      1. cross-app-be has no FK to that table (cross-service id) and treats it
         as an opaque number — same anti-pattern we just cleaned up for
         tax/discount/code types, where Hacienda code strings are the
         canonical identifier.

      2. Every product in production had the model-side default value 85,
         which doesn't exist in `measurement_units` (table starts at id=203).
         So the FE line-detail translation `productUnitToCode(85)` returned
         undefined and silently dropped the unit on every sales line.

    Replace with `unit_measure VARCHAR(20)` carrying the canonical Hacienda
    unit-of-measure code ("Unid", "Sp", "kg", "m", ...).

    Live state: 40 products, all with the meaningless default 85 — no real
    data to migrate.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "replace_unit_id_w_measure"
down_revision: Union[str, None] = "drop_legacy_cabys_name_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products", sa.Column("unit_measure", sa.String(length=20), nullable=True))
    op.drop_column("products", "unit_id")


def downgrade() -> None:
    op.add_column("products", sa.Column("unit_id", sa.Integer(), nullable=True))
    op.drop_column("products", "unit_measure")
