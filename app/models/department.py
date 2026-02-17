from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class Department(Base, AuditMixin):
    __tablename__ = "departments"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[str] = mapped_column(String(50), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.client_id"), nullable=False
    )
    department_code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    supplier_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="departments")

    __table_args__ = (
        Index("idx_department_client_code", "client_id", "department_code", unique=True),
        Index("idx_department_company_id", "company_id"),
        Index("idx_department_client_id", "client_id"),
    )
