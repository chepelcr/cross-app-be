"""Give an order line the same fiscal shape as a document line.

An order line was missing most of what a `DetalleLinea` carries, so anything the
POS knew that the line had no column for was lost the moment a sale became a
pedido — and had to be guessed back when the pedido was billed:

* ``codes`` — **the line's own product codes**. The response derived
  internal/vendor/buyer codes from the linked PRODUCT's `codes` array, which
  holds whatever the most recent import wrote. Two chains use two different
  buyer article codes for the same product, and each import overwrote the other,
  so an order could show the codes of a different customer's order entirely. The
  spreadsheet gives each line its own codes; they belong on the line.
* ``unit_measure`` — Hacienda requires `UnidadMedida` on every line. With no
  column, billing a pedido fell back to "Unid" — wrong for anything sold by
  weight or volume.
* ``base_amount`` + ``iva_collected_factory`` — the two situations where the
  taxable base may legitimately depart from the subtotal (tax code 07, and VAT
  settled at the factory). Dropping them silently re-priced the line.
* ``commercial_unit_measure``, ``customs_part`` — the rest of the document line.

Revision ID: bd0e1f2a3b4c
Revises: ac9d0e1f2a3b
Create Date: 2026-09-10 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "bd0e1f2a3b4c"
down_revision: Union[str, Sequence[str], None] = "ac9d0e1f2a3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "crossdocking_order_lines"

_COLUMNS = (
    # Canonical `[{code_type_id, number}]`, the same shape the document line and
    # the product both use.
    sa.Column("codes", sa.JSON(), nullable=True),
    sa.Column("unit_measure", sa.String(length=20), nullable=True),
    sa.Column("commercial_unit_measure", sa.String(length=50), nullable=True),
    sa.Column("base_amount", sa.Numeric(18, 5), nullable=True),
    sa.Column("iva_collected_factory", sa.String(length=2), nullable=True),
    sa.Column("customs_part", sa.String(length=50), nullable=True),
)


def upgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}
    for column in _COLUMNS:
        if column.name not in existing:
            op.add_column(_TABLE, column.copy())


def downgrade() -> None:
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns(_TABLE)}
    for column in reversed(_COLUMNS):
        if column.name in existing:
            op.drop_column(_TABLE, column.name)
