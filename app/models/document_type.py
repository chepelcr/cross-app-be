from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DocumentType(Base):
    """Read-only ORM mapping to the document_types table managed by data-services.

    This model maps to the shared PostgreSQL table. Never write to this table
    from cross-app-be — it is owned by the data-services application.
    """
    __tablename__ = "document_types"
    __table_args__ = (
        Index("ix_document_types_code", "code"),
        Index("ix_document_types_country_code", "country_code"),
        Index("ix_document_types_status", "status"),
        {"extend_existing": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_on: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_on: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_on: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
