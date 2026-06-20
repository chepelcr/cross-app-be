"""drop description from product codes JSONB

Strips the legacy `description` key from every entry of `products.codes`
(JSONB). The `ProductCodeDTO` / `ProductCodeResponse` schemas no longer
carry that field — codes are now `{code_type_id, number}` only. The
free-text "why" lives exclusively on discount rows via `reason`.

Mirrors the JSONB-key-strip approach used by v2d3e4f5a6b7 for
`discounts[].nature_discount`. The value is discarded (no copy target).

Revision ID: w3e4f5a6b7c8
Revises: v2d3e4f5a6b7
Create Date: 2026-05-22 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "w3e4f5a6b7c8"
down_revision: Union[str, Sequence[str], None] = "v2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Strip the `description` key from every entry of `products.codes`.
    # The JSONB `-` operator removes a top-level key from each element.
    op.execute(
        """
        UPDATE products
        SET codes = (
            SELECT jsonb_agg(c - 'description')
            FROM jsonb_array_elements(products.codes) AS c
        )
        WHERE codes IS NOT NULL
          AND jsonb_typeof(codes) = 'array'
          AND jsonb_array_length(codes) > 0
          AND EXISTS (
              SELECT 1
              FROM jsonb_array_elements(products.codes) AS c2
              WHERE c2 ? 'description'
          );
        """
    )


def downgrade() -> None:
    # Best-effort: re-introduce a null `description` key on each entry so
    # the prior schema shape is restored. Original values cannot be
    # recovered.
    op.execute(
        """
        UPDATE products
        SET codes = (
            SELECT jsonb_agg(
                CASE
                    WHEN c ? 'description' THEN c
                    ELSE jsonb_set(c, '{description}', 'null'::jsonb, true)
                END
            )
            FROM jsonb_array_elements(products.codes) AS c
        )
        WHERE codes IS NOT NULL
          AND jsonb_typeof(codes) = 'array'
          AND jsonb_array_length(codes) > 0;
        """
    )
