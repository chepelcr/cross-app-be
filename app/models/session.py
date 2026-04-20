from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """
    Session model for sales sessions (matches/shifts).
    Table name is 'sales_sessions' to avoid conflict with web sessions.
    """
    __tablename__ = "sales_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'match' or 'shift'
    context: Mapped[str] = mapped_column(String(50), nullable=False)  # 'gradas', 'mesa', or 'caja'
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expected_revenue: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    actual_revenue: Mapped[Optional[float]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("idx_sessions_org", "organization_id"),
        Index("idx_sessions_active", "organization_id", "is_active"),
        Index("idx_sessions_branch", "branch_id"),
        Index("idx_sessions_time", "start_time"),
    )
