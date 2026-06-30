"""add storefront pedido fields to crossdocking_orders (tracked anonymous order)

Revision ID: y5a6b7c8d9e0
Revises: x4f5a6b7c8d9
Create Date: 2026-06-20

Context (TSR-118 / storefront MVP W11):
    Adds the anonymous-storefront pedido fields to the ``crossdocking_orders``
    table so a guest visitor of a deployed storefront can place a tracked
    order (status 'pending') without a user account or a Client row:

      - tracking_number:  public tracking handle (also the document number)
      - customer_name / customer_phone:  the guest customer
      - delivery_method:  e.g. 'delivery' / 'pickup'
      - state_id / county_id / district_id / neighborhood_id:  structured CR
        address (data-be location cascade ids)
      - delivery_address:  dirección exacta (free text)

    ``crossdocking_orders`` is OWNED by this service (not a shared BeautyMarket
    table), so adding columns is clean. All columns are nullable — existing
    crossdocking-imported orders simply leave them NULL.

    NOTE: not yet applied — a human runs ``alembic upgrade head`` on rollout.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "y5a6b7c8d9e0"
down_revision: Union[str, Sequence[str], None] = "x4f5a6b7c8d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crossdocking_orders",
        sa.Column("tracking_number", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("customer_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("customer_phone", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("delivery_method", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("state_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("county_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("district_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("neighborhood_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "crossdocking_orders",
        sa.Column("delivery_address", sa.String(length=500), nullable=True),
    )
    op.create_index(
        "ix_crossdocking_orders_tracking_number",
        "crossdocking_orders",
        ["tracking_number"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_crossdocking_orders_tracking_number",
        table_name="crossdocking_orders",
    )
    op.drop_column("crossdocking_orders", "delivery_address")
    op.drop_column("crossdocking_orders", "neighborhood_id")
    op.drop_column("crossdocking_orders", "district_id")
    op.drop_column("crossdocking_orders", "county_id")
    op.drop_column("crossdocking_orders", "state_id")
    op.drop_column("crossdocking_orders", "delivery_method")
    op.drop_column("crossdocking_orders", "customer_phone")
    op.drop_column("crossdocking_orders", "customer_name")
    op.drop_column("crossdocking_orders", "tracking_number")
