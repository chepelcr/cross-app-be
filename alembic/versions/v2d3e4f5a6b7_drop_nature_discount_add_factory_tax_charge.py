"""drop nature_discount from product discounts JSONB, add factory_tax_charge_id

Two changes:
1. Strip the legacy `nature_discount` key from every entry of `products.discounts`
   (JSONB). When a real value lived there but `reason` was empty, migrate it onto
   `reason` first so we don't lose audit text. The DTOs no longer accept the key.
2. Add the new `products.factory_tax_charge_id` column for round-tripping the
   FE-captured data-services FK.

Revision ID: v2d3e4f5a6b7
Revises: u1c2d3e4f5a6
Create Date: 2026-05-22 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "v2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "u1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add the new factory_tax_charge_id column.
    op.add_column(
        "products",
        sa.Column("factory_tax_charge_id", sa.Integer(), nullable=True),
    )

    # 2) Migrate any meaningful `nature_discount` value onto `reason` (only when
    #    reason is null/empty), then strip the `nature_discount` key from every
    #    entry. Done in two passes so the value isn't lost before the key is
    #    removed. Skips the placeholder string "legacy" introduced by the prior
    #    migration — that wasn't user data.
    op.execute(
        """
        UPDATE products
        SET discounts = (
            SELECT jsonb_agg(
                CASE
                    WHEN (d ? 'nature_discount')
                         AND COALESCE(d->>'nature_discount', '') NOT IN ('', 'legacy')
                         AND COALESCE(d->>'reason', '') = ''
                    THEN jsonb_set(d, '{reason}', to_jsonb(d->>'nature_discount'), true)
                    ELSE d
                END
            )
            FROM jsonb_array_elements(products.discounts) AS d
        )
        WHERE discounts IS NOT NULL
          AND jsonb_typeof(discounts) = 'array'
          AND jsonb_array_length(discounts) > 0
          AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements(products.discounts) AS d2
              WHERE (d2 ? 'nature_discount')
                AND COALESCE(d2->>'nature_discount', '') NOT IN ('', 'legacy')
                AND COALESCE(d2->>'reason', '') = ''
          );
        """
    )

    # Strip the `nature_discount` key from every entry — the JSONB `-` operator
    # removes a top-level key.
    op.execute(
        """
        UPDATE products
        SET discounts = (
            SELECT jsonb_agg(d - 'nature_discount')
            FROM jsonb_array_elements(products.discounts) AS d
        )
        WHERE discounts IS NOT NULL
          AND jsonb_typeof(discounts) = 'array'
          AND jsonb_array_length(discounts) > 0
          AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements(products.discounts) AS d2
              WHERE d2 ? 'nature_discount'
          );
        """
    )


def downgrade() -> None:
    # Best-effort: for code-99 entries, copy `reason` back into a
    # `nature_discount` key so the previous validator's expectation is honoured.
    op.execute(
        """
        UPDATE products
        SET discounts = (
            SELECT jsonb_agg(
                CASE
                    WHEN d->>'discount_type_id' = '99'
                         AND COALESCE(d->>'reason', '') <> ''
                    THEN jsonb_set(d, '{nature_discount}', to_jsonb(d->>'reason'), true)
                    ELSE d
                END
            )
            FROM jsonb_array_elements(products.discounts) AS d
        )
        WHERE discounts IS NOT NULL
          AND jsonb_typeof(discounts) = 'array'
          AND jsonb_array_length(discounts) > 0;
        """
    )

    op.drop_column("products", "factory_tax_charge_id")
