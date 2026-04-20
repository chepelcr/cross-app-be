from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Computed

from app.models.base import Base, TimestampMixin


class Closing(Base, TimestampMixin):
    """
    Closing model for cash register closings at end of session.
    Tracks expected vs declared amounts and calculates differences.
    """
    __tablename__ = "closings"

    closing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_sessions.session_id", ondelete="CASCADE"), nullable=False
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assignments.assignment_id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False
    )
    terminal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("terminals.terminal_id", ondelete="SET NULL"), nullable=True
    )
    cashier_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Expected amounts (from system)
    expected_cash: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False, server_default="0"
    )
    expected_sinpe: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False, server_default="0"
    )
    expected_card: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False, server_default="0"
    )
    expected_total: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False, server_default="0"
    )
    
    # Declared amounts (from cashier)
    declared_cash: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False
    )
    declared_sinpe: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False
    )
    declared_card: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False
    )
    declared_total: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=12, scale=2), nullable=False
    )
    
    # Differences (calculated/generated columns)
    cash_difference: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2),
        Computed("(declared_cash - expected_cash)"),
        nullable=True
    )
    sinpe_difference: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2),
        Computed("(declared_sinpe - expected_sinpe)"),
        nullable=True
    )
    card_difference: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2),
        Computed("(declared_card - expected_card)"),
        nullable=True
    )
    total_difference: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(precision=12, scale=2),
        Computed("(declared_total - expected_total)"),
        nullable=True
    )
    
    # Additional fields
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="pending"
    )  # 'pending', 'approved', 'rejected'
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_closings_session", "session_id"),
        Index("idx_closings_status", "organization_id", "status"),
        Index("idx_closings_branch", "branch_id"),
        Index("idx_closings_cashier", "cashier_id"),
        UniqueConstraint("assignment_id", name="uq_closings_assignment"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_closings_status"),
    )
