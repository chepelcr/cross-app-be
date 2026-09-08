from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, StatusMixin, TimestampMixin


class Table(Base, TimestampMixin, StatusMixin):
    """A place a cart can be held against: a restaurant table, or a bar tab.

    One model for both on purpose. A tab is the same object as a table — a
    named holding place for an order — so the bar vertical sets `is_dynamic`
    instead of getting a second mechanism. A dynamic row is created when the
    tab opens (name = the customer) and removed when it is paid; a static one
    is part of the floor plan and outlives the shift.

    Server-side rather than client-side because a shift change or a device swap
    must not lose an open table.
    """

    __tablename__ = "tables"

    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[str] = mapped_column(String(50), nullable=False)
    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.branch_id", ondelete="CASCADE"), nullable=False
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    #: Free label — "terraza", "barra", "salón" — not an enum: every venue
    #: names its own areas.
    zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    #: True for a bar tab created on the fly; False for the fixed floor plan.
    is_dynamic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    opened_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    #: Document tab currently held against this table, if any.
    held_document_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_tables_org", "organization_id"),
        Index("idx_tables_branch", "branch_id"),
        Index("idx_tables_branch_code", "branch_id", "code", unique=True),
    )
