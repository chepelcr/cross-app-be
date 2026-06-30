"""add products.is_offer (storefront Oferta flag) + index type, backfill type from is_service

Revision ID: x4f5a6b7c8d9
Revises: canon_prod_jsonb_keys, w3e4f5a6b7c8
Create Date: 2026-06-20

Context (TSR-118 / storefront MVP W10):
    Formalizes the product "kind" + storefront offer flag on the shared
    ``products`` table:

      1. ``type`` becomes a first-class kind (product | service | program).
         It already exists as VARCHAR(20) DEFAULT 'product'; this migration
         only ADDS an index on it (the env.py guard for shared tables permits
         additive index creation) and backfills ``type='service'`` for rows
         that historically only set the legacy ``is_service`` boolean.

      2. ``is_offer`` is a NEW boolean column — the storefront "Oferta" flag,
         orthogonal to the ``on_sale`` discount mechanic. Added NOT NULL with
         a server_default of false so existing rows are valid; the model-side
         default keeps new inserts consistent.

    ``products`` is a SHARED table (BeautyMarket) — this migration is strictly
    additive (one new column + one new index + a data backfill). It does not
    drop or alter any existing column.

    This is also a MERGE migration: it unifies the two pre-existing heads
    (``canon_prod_jsonb_keys`` from the product-fiscal branch and
    ``w3e4f5a6b7c8`` from the product-code-cleanup branch) into a single head.

    NOTE: not yet applied — a human runs ``alembic upgrade head`` on rollout.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "x4f5a6b7c8d9"
down_revision: Union[str, Sequence[str], None] = (
    "canon_prod_jsonb_keys",
    "w3e4f5a6b7c8",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. New storefront "Oferta" flag — NOT NULL with a server default so the
    #    add is safe against existing rows.
    op.add_column(
        "products",
        sa.Column(
            "is_offer",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index("ix_products_is_offer", "products", ["is_offer"])

    # 2. Index the now-first-class kind column for the type filter.
    op.create_index("ix_products_type", "products", ["type"])

    # 3. Backfill: rows that were marked as services via the legacy boolean
    #    but never got type set should read as type='service'.
    op.execute(
        "UPDATE products SET type = 'service' "
        "WHERE is_service = true AND (type IS NULL OR type = 'product')"
    )
    # Normalize any NULL/blank type to the canonical default.
    op.execute(
        "UPDATE products SET type = 'product' WHERE type IS NULL OR type = ''"
    )


def downgrade() -> None:
    op.drop_index("ix_products_type", table_name="products")
    op.drop_index("ix_products_is_offer", table_name="products")
    op.drop_column("products", "is_offer")
