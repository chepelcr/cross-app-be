from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class CrossDockingSalePoint(Base, AuditMixin):
    __tablename__ = "crossdocking_sale_points"

    sale_point_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("crossdocking_orders.order_id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    total_boxes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    total_units: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)

    # Normalized FK
    store_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.store_id"), nullable=True
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="crossdocking_sale_points")
    store: Mapped[Optional["Store"]] = relationship(foreign_keys=[store_id])
    items: Mapped[List["CrossDockingItem"]] = relationship(
        back_populates="sale_point", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_crossdocking_sp_order_id", "order_id"),
    )
