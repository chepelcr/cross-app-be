from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class Order(Base, AuditMixin):
    __tablename__ = "crossdocking_orders"

    order_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("organizations.id"), nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    creation_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delivery_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="pending")
    subtotal: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    discounts: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    net_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    taxes: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    grand_total: Mapped[Optional[float]] = mapped_column(Numeric(18, 5), nullable=True, default=0)
    total_quantities: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    line_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)
    document_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bgm011: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    order_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    event: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    latitude: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    longitude: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    crossdocking_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    nuevo_reporte_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    excel_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    crossdocking_excel_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confirmation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("crossdocking_confirmations.confirmation_id"), nullable=True
    )
    confirmation_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Normalized FK columns
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id"), nullable=True
    )
    deliver_to_store_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.store_id"), nullable=True
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.department_id"), nullable=True
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(foreign_keys=[company_id])
    client: Mapped[Optional["Client"]] = relationship(foreign_keys=[client_id])
    deliver_to_store: Mapped[Optional["Store"]] = relationship(foreign_keys=[deliver_to_store_id])
    department_rel: Mapped[Optional["Department"]] = relationship(foreign_keys=[department_id])
    lines: Mapped[List["OrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    crossdocking_sale_points: Mapped[List["CrossDockingSalePoint"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    confirmation: Mapped[Optional["Confirmation"]] = relationship(
        back_populates="orders"
    )

    __table_args__ = (
        Index("idx_order_company_id", "company_id"),
        Index("idx_order_document_number", "document_number"),
        Index("idx_order_company_document", "company_id", "document_number", unique=True),
    )
