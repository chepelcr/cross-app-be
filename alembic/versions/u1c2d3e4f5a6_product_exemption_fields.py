"""add product exemption / iva_collected_factory columns + backfill nature_discount

Revision ID: u1c2d3e4f5a6
Revises: t0b1c2d3e4f5
Create Date: 2026-05-22 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "u1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "t0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hacienda v4.4 Exoneracion block + IVACobradoFabrica indicator.
    op.add_column(
        "products",
        sa.Column("exemption_authorization_code", sa.String(length=2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("exempted_rate", sa.Numeric(4, 2), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("exemption_amount", sa.Numeric(18, 5), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("iva_collected_factory", sa.String(length=2), nullable=True),
    )

    # Backfill: legacy rows with a 99-type discount but no nature_discount field
    # would now fail the Pydantic validator on read. Stamp a placeholder so
    # round-trips remain green for pre-existing data.
    op.execute(
        """
        UPDATE products
        SET discounts = (
            SELECT jsonb_agg(
                CASE
                    WHEN d->>'discount_type_id' = '99'
                         AND (d ? 'nature_discount') = false
                    THEN d || jsonb_build_object('nature_discount', 'legacy')
                    WHEN d->>'discount_type_id' = '99'
                         AND COALESCE(d->>'nature_discount', '') = ''
                    THEN jsonb_set(d, '{nature_discount}', '"legacy"', true)
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
              WHERE d2->>'discount_type_id' = '99'
                AND COALESCE(d2->>'nature_discount', '') = ''
          );
        """
    )


def downgrade() -> None:
    op.drop_column("products", "iva_collected_factory")
    op.drop_column("products", "exemption_amount")
    op.drop_column("products", "exempted_rate")
    op.drop_column("products", "exemption_authorization_code")
