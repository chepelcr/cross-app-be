from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class CrossDockingItem(Base, AuditMixin):
    __tablename__ = "crossdocking_items"

    item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sale_point_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("crossdocking_sale_points.sale_point_id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    total_units: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    sent: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    missing: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)

    # Normalized FK
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id"), nullable=True
    )

    # Relationships
    sale_point: Mapped["CrossDockingSalePoint"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(foreign_keys=[product_id])

    __table_args__ = (
        Index("idx_crossdocking_item_sp_id", "sale_point_id"),
    )
