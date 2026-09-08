from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Time,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatusMixin, TimestampMixin


# ─── Bar (TSR-158) ──────────────────────────────────────────────────────────

class PriceSchedule(Base, TimestampMixin, StatusMixin):
    """A time window in which certain products cost something else — happy hour.

    Resolution is "highest `priority` active *now* wins", and the SERVER
    re-resolves it on submit: price is authority-critical, and a stale or
    tampered client clock must not set the price on a fiscal document.
    """

    __tablename__ = "price_schedules"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    #: ISO weekday numbers [1..7]; empty/None means every day.
    days_of_week: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    start_time: Mapped[Optional[str]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(Time, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    items: Mapped[List["PriceScheduleItem"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_price_schedules_org", "organization_id"),)


class PriceScheduleItem(Base, TimestampMixin):
    """What a schedule changes: a product's price, or a category's discount."""

    __tablename__ = "price_schedule_items"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("price_schedules.schedule_id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=True
    )
    # categories.id is a String PK, not a UUID — match it.
    category_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    price: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True)
    discount_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    schedule: Mapped["PriceSchedule"] = relationship(back_populates="items")

    __table_args__ = (Index("idx_price_schedule_items_schedule", "schedule_id"),)


# ─── Farmacia (TSR-159) ─────────────────────────────────────────────────────

class ProductLot(Base, TimestampMixin, StatusMixin):
    """A batch of a product with an expiry date.

    Drives FEFO (first expiry, first out) at the till. Also useful to a
    minisuper for perishables, which is why the capability is generic even
    though the module is named for the pharmacy.
    """

    __tablename__ = "product_lots"

    lot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    lot_code: Mapped[str] = mapped_column(String(50), nullable=False)
    expires_on: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=0)

    __table_args__ = (
        Index("idx_product_lots_product", "product_id"),
        Index("idx_product_lots_expiry", "product_id", "expires_on"),
        Index("idx_product_lots_code", "product_id", "lot_code", unique=True),
    )


class ControlledSale(Base, TimestampMixin):
    """Register entry for a controlled-substance sale.

    Append-only by design: a register that can be edited is not a register.
    Captured before checkout can complete, and exported per period.
    """

    __tablename__ = "controlled_sales"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    sale_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id"), nullable=True
    )

    buyer_id_type: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    buyer_id_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    buyer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prescriber_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prescription_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prescription_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sold_on: Mapped[Optional[str]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_controlled_sales_org", "organization_id"),
        Index("idx_controlled_sales_sold_on", "organization_id", "sold_on"),
    )


# ─── Ferretería (TSR-161) ───────────────────────────────────────────────────

class ProductUnit(Base, TimestampMixin, StatusMixin):
    """Sell in one unit, stock in another: buy a rollo, sell by the metro.

    Reaches the tax engine only through `quantity` and `unit_price`, so the
    Hacienda cascade is untouched — which is exactly why this is cheap.
    """

    __tablename__ = "product_units"

    product_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    #: data-be measurement-unit id (the catalog already exists).
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    #: How many BASE units one of these is worth.
    factor_to_base: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=1)
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    price_override: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True)

    __table_args__ = (
        Index("idx_product_units_product", "product_id"),
        Index("idx_product_units_uq", "product_id", "unit_code", unique=True),
    )


# ─── Agenda: salón AND taller (TSR-162) ─────────────────────────────────────

class Appointment(Base, TimestampMixin, StatusMixin):
    """A booked slot.

    One model for two verticals: a salón books a person, a taller books a
    person AND a vehicle — hence the nullable `asset_id`. Completing one opens
    a POS tab (a work-order tab when the asset is set), which is the point of
    keeping the calendar inside the POS.
    """

    __tablename__ = "appointments"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="SET NULL"), nullable=True
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id", ondelete="SET NULL"), nullable=True
    )
    #: The collaborator the slot belongs to — the agenda's columns.
    staff_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    service_product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    #: Taller only: which vehicle/equipment is coming in.
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_assets.asset_id", ondelete="SET NULL"), nullable=True
    )

    starts_at: Mapped[Optional[str]] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    #: booked | confirmed | completed | cancelled | no_show
    appointment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="booked")
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    #: Set once the slot turned into a sale/order, so it is not billed twice.
    converted_document_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_appointments_org_start", "organization_id", "starts_at"),
        Index("idx_appointments_staff", "staff_user_id", "starts_at"),
        Index("idx_appointments_client", "client_id"),
    )


class CommissionRule(Base, TimestampMixin, StatusMixin):
    """Percentage a collaborator earns. Most specific rule wins.

    Specificity order: product > category > staff-wide > org-wide. Resolved in
    the service, not by a query, so the precedence is readable in one place.
    """

    __tablename__ = "commission_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    staff_user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=True
    )
    category_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True
    )
    percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)

    __table_args__ = (Index("idx_commission_rules_org", "organization_id"),)


# ─── Servicios (TSR-160) ────────────────────────────────────────────────────

class RecurringInvoice(Base, TimestampMixin, StatusMixin):
    """A document template that reissues on a cadence.

    A run creates a DRAFT — it never transmits to Hacienda on its own. Emitting
    a fiscal document is a decision a person makes, not a cron job.
    """

    __tablename__ = "recurring_invoices"

    recurring_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    #: The cart/document to reissue, stored whole so a catalog edit does not
    #: silently change what the customer agreed to.
    template_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    #: monthly | weekly | yearly
    cadence: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    next_run_on: Mapped[Optional[str]] = mapped_column(Date, nullable=True)
    last_run_on: Mapped[Optional[str]] = mapped_column(Date, nullable=True)

    __table_args__ = (
        Index("idx_recurring_org", "organization_id"),
        Index("idx_recurring_next_run", "next_run_on"),
    )
