from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Assignment(Base, TimestampMixin):
    """
    Assignment model for cashier assignments to branches/terminals during sessions.
    Links users (cashiers) to branches and terminals for specific sales sessions.
    
    Status values: 1=Active, 2=Inactive, 3=Deleted
    """
    __tablename__ = "assignments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sales_sessions.session_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False
    )
    terminal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("terminals.terminal_id", ondelete="SET NULL"), nullable=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # 'cashier' or 'supervisor'
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1=Active, 2=Inactive, 3=Deleted
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("idx_assignments_session", "session_id"),
        Index("idx_assignments_user", "user_id"),
        Index("idx_assignments_branch", "branch_id"),
        Index("idx_assignments_status", "session_id", "status"),
        # Constraint: User can only have one active assignment at a time
        Index("idx_user_active_assignment", "user_id", "status", 
              unique=True, postgresql_where=text("status = 1")),
    )
