from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, StatusMixin, TimestampMixin


class Sale(Base, TimestampMixin, StatusMixin):
    __tablename__ = "sales"

    sale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    assignment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Branch/terminal stored both as int codes (for easy reporting) and UUIDs (FK integrity)
    branch_code: Mapped[int] = mapped_column(Integer, nullable=False)
    terminal_code: Mapped[int] = mapped_column(Integer, nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="RESTRICT"), nullable=False
    )
    terminal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("terminals.terminal_id", ondelete="RESTRICT"), nullable=False
    )
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id", ondelete="SET NULL"), nullable=True
    )

    # Hacienda document metadata
    document_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    activity_code: Mapped[str] = mapped_column(String(20), nullable=False)
    sale_condition_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    credit_term: Mapped[str] = mapped_column(String(10), nullable=False, default="0")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    copy_emails: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Receiver info (denormalized at time of sale)
    receiver_id_type: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    receiver_id_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receiver_business_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receiver_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receiver_state_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    receiver_county_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    receiver_district_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    receiver_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payments (e.g. [{"type": 1, "amount": 5000.0}, {"type": 4, "amount": 2000.0}])
    payments: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Totals
    subtotal: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 5), nullable=False)

    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("idx_sales_org", "organization_id"),
        Index("idx_sales_org_branch", "organization_id", "branch_code"),
        Index("idx_sales_org_created", "organization_id", "created_on"),
        Index("idx_sales_assignment", "assignment_id"),
    )
