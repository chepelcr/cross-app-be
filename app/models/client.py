from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class Client(Base, AuditMixin):
    __tablename__ = "clients"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[str] = mapped_column(String(50), nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    client_gln: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    stores: Mapped[List["Store"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    departments: Mapped[List["Department"]] = relationship(back_populates="client", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_client_company_gln", "company_id", "client_gln", unique=True),
        Index("idx_client_company_id", "company_id"),
    )
