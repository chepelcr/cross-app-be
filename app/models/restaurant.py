from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, StatusMixin, TimestampMixin


class ComboItem(Base, TimestampMixin):
    """A component of a combo product.

    The combo carries its own `price` — it is NOT the sum of its parts, which is
    the whole point of a combo. The components exist so the POS can explode the
    line at add-to-cart time: each one keeps its own CABYS and IVA rate, and a
    combo mixing 13% and exempt items cannot be represented as one flat line on
    a fiscal document.
    """

    __tablename__ = "combo_items"

    combo_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    combo_product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=1)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_combo_items_combo", "combo_product_id"),
        Index("idx_combo_items_product", "product_id"),
    )


class ModifierGroup(Base, TimestampMixin, StatusMixin):
    """A question asked about a line: "¿punto de cocción?", "¿extras?"."""

    __tablename__ = "modifier_groups"

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    #: Selection bounds. `required` is min>=1 spelled out, kept separate because
    #: "pick at least one" and "pick exactly one" read differently in the UI.
    min_select: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_select: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    modifiers: Mapped[List["Modifier"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_modifier_groups_org", "organization_id"),)


class Modifier(Base, TimestampMixin, StatusMixin):
    """One choice inside a group.

    Two shapes, and the difference is fiscal, not cosmetic:

    * `price_delta` only — rides the parent line as a price adjustment.
    * `product_id` set — becomes its OWN cart line, because a real product has
      its own CABYS and IVA rate and must not inherit the parent's.
    """

    __tablename__ = "modifiers"

    modifier_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modifier_groups.group_id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_delta: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=0)
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    group: Mapped["ModifierGroup"] = relationship(back_populates="modifiers")

    __table_args__ = (Index("idx_modifiers_group", "group_id"),)


class ProductModifierGroup(Base, TimestampMixin):
    """Which groups a product asks about."""

    __tablename__ = "product_modifier_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("modifier_groups.group_id", ondelete="CASCADE"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_product_modifier_groups_uq", "product_id", "group_id", unique=True),
    )


class KitchenStation(Base, TimestampMixin, StatusMixin):
    """Where a comanda prints: cocina caliente, barra, postres.

    `printer_target` is a NAME, not a driver. A browser cannot address a thermal
    printer directly, so this maps to a print destination the user picks in the
    OS dialog. Anything more (ESC/POS via a local agent) is out of scope.
    """

    __tablename__ = "kitchen_stations"

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    printer_target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_kitchen_stations_org", "organization_id"),
        Index("idx_kitchen_stations_branch", "branch_id"),
    )


class ProductStation(Base, TimestampMixin):
    """Routes a product to zero or more kitchen stations."""

    __tablename__ = "product_stations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    product_id: Mapped[str] = mapped_column(
        String, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("kitchen_stations.station_id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        Index("idx_product_stations_uq", "product_id", "station_id", unique=True),
    )
