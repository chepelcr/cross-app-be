from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class OrderLine(Base, AuditMixin):
    __tablename__ = "crossdocking_order_lines"

    line_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("crossdocking_orders.order_id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    quantity_ordered: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    units_ordered: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    discount: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    line_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    tax: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    quantity_dispatched: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    dispatch_rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quantity_received: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    article_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- Manual-order line detail (TSR-152) -------------------------------
    # A hand-captured line is not always a catalog product, and billing the
    # order later needs its CABYS — fabricating one would put the wrong rate on
    # a fiscal document.
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cabys: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    #: Unit price BEFORE tax, distinct from `unit_price` on imported lines.
    net_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True)
    #: Per-line breakdowns, JSON rather than child tables: a pedido is not a
    #: fiscal document and is excluded from the D-150 report, so nothing queries
    #: these per tax code. Promote to `order_line_taxes` if that ever changes.
    taxes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    discounts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # --- The rest of the document line (migration `bd0e1f2a3b4c`) ----------
    #: The LINE's own product codes, canonical `[{code_type_id, number}]`.
    #:
    #: Not the product's. A chain assigns its own buyer article code, the
    #: product's `codes` array holds whatever the last import wrote, and two
    #: customers ordering the same product overwrite each other there — so an
    #: order could display a different customer's codes. The spreadsheet gives
    #: every line its own; those are the ones that belong to this order.
    codes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    #: Hacienda `UnidadMedida`. Required on every document line, so without it
    #: billing the pedido has to fall back to "Unid".
    unit_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    commercial_unit_measure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    #: Editable taxable base — legal only for tax code 07 or
    #: `iva_collected_factory == "01"`, and validated as such downstream.
    base_amount: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True)
    #: `IVACobradoFabrica`: "01" VAT settled at factory, "02" exempt by regime.
    iva_collected_factory: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    customs_part: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Normalized FK
    product_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("products.id"), nullable=True
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship(foreign_keys=[product_id])

    __table_args__ = (
        Index("idx_order_line_order_id", "order_id"),
    )
