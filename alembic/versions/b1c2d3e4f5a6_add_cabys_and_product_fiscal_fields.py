"""Add cabys table and product fiscal fields.

Revision ID: b1c2d3e4f5a6
Revises: a2b3c4d5e6f7
Create Date: 2026-02-24

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the cabys catalog table
    op.create_table(
        "cabys",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("code", sa.String(13), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("type", sa.Integer, nullable=False),
    )
    op.create_index("idx_cabys_code", "cabys", ["code"], unique=True)

    # Add fiscal/tax columns to products (shared table — additions only)
    op.add_column(
        "products",
        sa.Column("cabys_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("unit_id", sa.Integer, nullable=True, server_default="85"),
    )
    op.add_column(
        "products",
        sa.Column("commercial_unit_measure", sa.String(50), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_packaged",
            sa.Boolean,
            nullable=True,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "quantity",
            sa.Numeric(10, 3),
            nullable=True,
            server_default="1",
        ),
    )
    op.add_column(
        "products",
        sa.Column("unit_price", sa.Numeric(10, 5), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("customs_part", sa.String(50), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column(
            "codes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "discounts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "taxes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "products",
        sa.Column("base_amount", sa.Numeric(10, 5), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("sale_price", sa.Numeric(10, 5), nullable=True),
    )

    # Foreign key from products.cabys_id → cabys.id
    op.create_foreign_key(
        "fk_products_cabys_id",
        "products",
        "cabys",
        ["cabys_id"],
        ["id"],
    )

    # Backfill sensible defaults for existing rows
    op.execute(
        """
        UPDATE products
        SET
            unit_id     = 85,
            is_packaged = FALSE,
            quantity    = 1,
            codes       = '[]'::jsonb,
            discounts   = '[]'::jsonb,
            taxes       = '[]'::jsonb,
            sale_price  = price
        WHERE unit_id IS NULL
        """
    )


def downgrade() -> None:
    # Drop the cabys table (owned entirely by this app)
    op.drop_constraint("fk_products_cabys_id", "products", type_="foreignkey")
    op.drop_index("idx_cabys_code", table_name="cabys")
    op.drop_table("cabys")

    # Products columns: intentional no-op.
    # Per env.py policy, we never drop columns from shared tables.
