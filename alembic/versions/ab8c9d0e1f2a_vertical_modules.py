"""vertical modules: restaurant, bar, farmacia, ferretería, agenda, servicios

One migration for every vertical table (TSR-154 / 158 / 159 / 160 / 161 / 162)
plus the product-level flags they read. Grouped deliberately: they share no
data, so ordering between them does not matter, and one revision keeps the
`business_type` rollout a single step.

Everything is additive — new tables, new nullable/defaulted product columns.
An organization that enables none of these verticals is unaffected.

Revision ID: ab8c9d0e1f2a
Revises: aa7b8c9d0e1f
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ab8c9d0e1f2a"
down_revision: Union[str, None] = "aa7b8c9d0e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID_PK = dict(primary_key=True, server_default=sa.text("gen_random_uuid()"))


def _audit():
    return [
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_on", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.Column("deleted_on", sa.DateTime(), nullable=True),
    ]


def _timestamps():
    return [
        sa.Column("created_on", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_on", sa.DateTime(), nullable=True),
        sa.Column("deleted_on", sa.DateTime(), nullable=True),
    ]


PRODUCT_FLAGS = [
    ("is_combo", sa.Boolean(), "false"),
    ("is_age_restricted", sa.Boolean(), "false"),
    ("is_lot_tracked", sa.Boolean(), "false"),
    ("is_controlled", sa.Boolean(), "false"),
]

NEW_TABLES = [
    "product_stations", "kitchen_stations", "product_modifier_groups",
    "modifiers", "modifier_groups", "combo_items", "tables",
    "price_schedule_items", "price_schedules", "product_lots",
    "controlled_sales", "product_units", "appointments", "commission_rules",
    "recurring_invoices",
]


def upgrade() -> None:
    # ── Product flags ────────────────────────────────────────────────────
    for name, type_, default in PRODUCT_FLAGS:
        op.add_column(
            "products",
            sa.Column(name, type_, nullable=False, server_default=sa.text(default)),
        )
    op.add_column("products", sa.Column("duration_minutes", sa.Integer(), nullable=True))

    # ── Restaurant: mesas / tabs ─────────────────────────────────────────
    op.create_table(
        "tables",
        sa.Column("table_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column(
            "branch_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("seats", sa.Integer(), nullable=True),
        sa.Column("zone", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        # A bar tab is a dynamic table, not a second mechanism.
        sa.Column("is_dynamic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("opened_by", sa.String(255), nullable=True),
        sa.Column("held_document_id", sa.String(255), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=True),
        *_audit(),
    )
    op.create_index("idx_tables_org", "tables", ["organization_id"])
    op.create_index("idx_tables_branch", "tables", ["branch_id"])
    op.create_index("idx_tables_branch_code", "tables", ["branch_id", "code"], unique=True)

    # ── Restaurant: combos ───────────────────────────────────────────────
    op.create_table(
        "combo_items",
        sa.Column("combo_item_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("combo_product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 5), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("idx_combo_items_combo", "combo_items", ["combo_product_id"])
    op.create_index("idx_combo_items_product", "combo_items", ["product_id"])

    # ── Restaurant: modifiers ────────────────────────────────────────────
    op.create_table(
        "modifier_groups",
        sa.Column("group_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("min_select", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_select", sa.Integer(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_modifier_groups_org", "modifier_groups", ["organization_id"])

    op.create_table(
        "modifiers",
        sa.Column("modifier_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modifier_groups.group_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("price_delta", sa.Numeric(18, 5), nullable=False, server_default="0"),
        # A modifier linked to a real product becomes its own cart line, so its
        # CABYS and IVA rate are its own.
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_modifiers_group", "modifiers", ["group_id"])

    op.create_table(
        "product_modifier_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("modifier_groups.group_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
    )
    op.create_index("idx_product_modifier_groups_uq", "product_modifier_groups", ["product_id", "group_id"], unique=True)

    # ── Restaurant: comandas ─────────────────────────────────────────────
    op.create_table(
        "kitchen_stations",
        sa.Column("station_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        # A print destination name, not a driver: browsers cannot address a
        # thermal printer directly.
        sa.Column("printer_target", sa.String(100), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_kitchen_stations_org", "kitchen_stations", ["organization_id"])
    op.create_index("idx_kitchen_stations_branch", "kitchen_stations", ["branch_id"])

    op.create_table(
        "product_stations",
        sa.Column("id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("kitchen_stations.station_id", ondelete="CASCADE"), nullable=False),
        *_timestamps(),
    )
    op.create_index("idx_product_stations_uq", "product_stations", ["product_id", "station_id"], unique=True)

    # ── Bar: happy hour ──────────────────────────────────────────────────
    op.create_table(
        "price_schedules",
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("days_of_week", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_price_schedules_org", "price_schedules", ["organization_id"])

    op.create_table(
        "price_schedule_items",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("schedule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("price_schedules.schedule_id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=True),
        sa.Column("category_id", sa.String(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("price", sa.Numeric(18, 5), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        *_timestamps(),
    )
    op.create_index("idx_price_schedule_items_schedule", "price_schedule_items", ["schedule_id"])

    # ── Farmacia ─────────────────────────────────────────────────────────
    op.create_table(
        "product_lots",
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lot_code", sa.String(50), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 5), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_product_lots_product", "product_lots", ["product_id"])
    # FEFO reads this one.
    op.create_index("idx_product_lots_expiry", "product_lots", ["product_id", "expires_on"])
    op.create_index("idx_product_lots_code", "product_lots", ["product_id", "lot_code"], unique=True)

    op.create_table(
        "controlled_sales",
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("sale_id", sa.String(255), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("buyer_id_type", sa.String(4), nullable=True),
        sa.Column("buyer_id_number", sa.String(50), nullable=True),
        sa.Column("buyer_name", sa.String(255), nullable=True),
        sa.Column("prescriber_code", sa.String(50), nullable=True),
        sa.Column("prescription_number", sa.String(50), nullable=True),
        sa.Column("prescription_image_url", sa.String(500), nullable=True),
        sa.Column("sold_on", sa.DateTime(), nullable=True),
        *_timestamps(),
    )
    op.create_index("idx_controlled_sales_org", "controlled_sales", ["organization_id"])
    op.create_index("idx_controlled_sales_sold_on", "controlled_sales", ["organization_id", "sold_on"])

    # ── Ferretería ───────────────────────────────────────────────────────
    op.create_table(
        "product_units",
        sa.Column("product_unit_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("unit_code", sa.String(20), nullable=True),
        sa.Column("factor_to_base", sa.Numeric(18, 5), nullable=False, server_default="1"),
        sa.Column("is_base", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("price_override", sa.Numeric(18, 5), nullable=True),
        *_audit(),
    )
    op.create_index("idx_product_units_product", "product_units", ["product_id"])
    op.create_index("idx_product_units_uq", "product_units", ["product_id", "unit_code"], unique=True)

    # ── Agenda (salón AND taller) ────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("appointment_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("branches.branch_id", ondelete="SET NULL"), nullable=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.client_id", ondelete="SET NULL"), nullable=True),
        sa.Column("staff_user_id", sa.String(255), nullable=True),
        sa.Column("service_product_id", sa.String(), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        # Nullable: a salón books a person, a taller books a person AND a vehicle.
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("client_assets.asset_id", ondelete="SET NULL"), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("appointment_status", sa.String(20), nullable=False, server_default="booked"),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("converted_document_id", sa.String(255), nullable=True),
        *_audit(),
    )
    op.create_index("idx_appointments_org_start", "appointments", ["organization_id", "starts_at"])
    op.create_index("idx_appointments_staff", "appointments", ["staff_user_id", "starts_at"])
    op.create_index("idx_appointments_client", "appointments", ["client_id"])

    op.create_table(
        "commission_rules",
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("staff_user_id", sa.String(255), nullable=True),
        sa.Column("product_id", sa.String(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=True),
        sa.Column("category_id", sa.String(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=True),
        sa.Column("percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        *_audit(),
    )
    op.create_index("idx_commission_rules_org", "commission_rules", ["organization_id"])

    # ── Servicios ────────────────────────────────────────────────────────
    op.create_table(
        "recurring_invoices",
        sa.Column("recurring_id", postgresql.UUID(as_uuid=True), **UUID_PK),
        sa.Column("organization_id", sa.String(50), nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("template_payload", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("cadence", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("next_run_on", sa.Date(), nullable=True),
        sa.Column("last_run_on", sa.Date(), nullable=True),
        *_audit(),
    )
    op.create_index("idx_recurring_org", "recurring_invoices", ["organization_id"])
    op.create_index("idx_recurring_next_run", "recurring_invoices", ["next_run_on"])


def downgrade() -> None:
    for table in NEW_TABLES:
        op.drop_table(table)
    op.drop_column("products", "duration_minutes")
    for name, _, _ in reversed(PRODUCT_FLAGS):
        op.drop_column("products", name)
