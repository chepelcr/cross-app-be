"""manual orders + client assets (TSR-152 / TSR-163)

Gives `crossdocking_orders` and `crossdocking_order_lines` what a hand-captured
pedido needs, and adds the per-client asset catalog a taller's work orders hang
off.

Notes on shape:

* No new address columns. The storefront pedido (y5a6b7c8d9e0) already added
  state/county/district/neighborhood + delivery_address, and the manual order's
  `receiver` / `custom` delivery modes write into exactly those. Likewise
  `deliver_to_store_id` and `department_id` already exist.
* Line tax/discount breakdowns are JSON, not child tables: a pedido is not a
  fiscal document and is excluded from the D-150 report, so nothing queries them
  per tax code.
* `idempotency_key` is uniquely indexed per company but only where NOT NULL, so
  the millions of imported rows without one do not collide.

Revision ID: aa7b8c9d0e1f
Revises: z6b7c8d9e0f1
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "aa7b8c9d0e1f"
down_revision: Union[str, None] = "z6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ORDER_COLUMNS = [
    ("source", sa.String(16), "'import'"),
    ("created_by", sa.String(255), None),
    ("assignment_id", sa.String(255), None),
    ("branch_number", sa.Integer(), None),
    ("terminal_number", sa.Integer(), None),
    ("currency_code", sa.String(3), "'CRC'"),
    ("exchange_rate", sa.Numeric(18, 5), "1"),
    ("delivery_location_name", sa.String(255), None),
    ("activity_code", sa.String(20), None),
    ("sale_condition", sa.String(10), None),
    ("credit_term", sa.String(10), None),
    ("idempotency_key", sa.String(128), None),
    ("odometer", sa.BigInteger(), None),
    ("reported_issue", sa.String(500), None),
    ("invoice_sale_id", sa.String(255), None),
    ("invoice_document_type", sa.String(8), None),
    ("invoice_consecutive_number", sa.String(50), None),
    ("invoice_document_key", sa.String(100), None),
    ("invoice_issued_on", sa.String(30), None),
]

LINE_COLUMNS = [
    ("description", sa.String(500)),
    ("cabys", sa.String(13)),
    ("net_price", sa.Numeric(18, 5)),
]


def upgrade() -> None:
    # ── client_assets ────────────────────────────────────────────────────
    op.create_table(
        "client_assets",
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.client_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("identifier", sa.String(50), nullable=False),
        sa.Column("kind", sa.String(50), nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_on", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.Column("deleted_on", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_client_asset_org", "client_assets", ["organization_id"])
    op.create_index("idx_client_asset_client", "client_assets", ["client_id"])
    op.create_index(
        "idx_client_asset_client_identifier",
        "client_assets",
        ["client_id", "identifier"],
        unique=True,
    )

    # ── crossdocking_orders ──────────────────────────────────────────────
    for name, type_, default in ORDER_COLUMNS:
        op.add_column(
            "crossdocking_orders",
            sa.Column(name, type_, nullable=True, server_default=sa.text(default) if default else None),
        )
    op.add_column(
        "crossdocking_orders",
        sa.Column("payments", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_asset_id",
        "crossdocking_orders",
        "client_assets",
        ["asset_id"],
        ["asset_id"],
    )

    # Everything already in the table arrived through the Excel importer.
    op.execute("UPDATE crossdocking_orders SET source = 'import' WHERE source IS NULL")
    # …except storefront pedidos, which name themselves in order_type.
    op.execute(
        "UPDATE crossdocking_orders SET source = 'storefront' "
        "WHERE order_type = 'storefront'"
    )

    op.create_index("idx_order_source", "crossdocking_orders", ["company_id", "source"])
    op.create_index(
        "idx_order_idempotency",
        "crossdocking_orders",
        ["company_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    # ── crossdocking_order_lines ─────────────────────────────────────────
    for name, type_ in LINE_COLUMNS:
        op.add_column("crossdocking_order_lines", sa.Column(name, type_, nullable=True))
    for name in ("taxes", "discounts"):
        op.add_column(
            "crossdocking_order_lines",
            sa.Column(name, postgresql.JSON(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    for name in ("taxes", "discounts"):
        op.drop_column("crossdocking_order_lines", name)
    for name, _ in LINE_COLUMNS:
        op.drop_column("crossdocking_order_lines", name)

    op.drop_index("idx_order_idempotency", table_name="crossdocking_orders")
    op.drop_index("idx_order_source", table_name="crossdocking_orders")
    op.drop_constraint("fk_orders_asset_id", "crossdocking_orders", type_="foreignkey")
    op.drop_column("crossdocking_orders", "asset_id")
    op.drop_column("crossdocking_orders", "payments")
    for name, _, _ in reversed(ORDER_COLUMNS):
        op.drop_column("crossdocking_orders", name)

    op.drop_index("idx_client_asset_client_identifier", table_name="client_assets")
    op.drop_index("idx_client_asset_client", table_name="client_assets")
    op.drop_index("idx_client_asset_org", table_name="client_assets")
    op.drop_table("client_assets")
