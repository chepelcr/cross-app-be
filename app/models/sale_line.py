from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from app.models.base import Base, TimestampMixin


class SaleLine(Base, TimestampMixin):
    __tablename__ = "sale_lines"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales.sale_id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False)
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    net_price: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False)
    discount_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    tax_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=13)
    line_total: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False)

    __table_args__ = (
        Index("idx_sale_lines_sale_id", "sale_id"),
    )
