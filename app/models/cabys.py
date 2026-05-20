from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Cabys(Base):
    """CABYS catalog table for Costa Rica Hacienda e-invoicing.

    Source of truth: data-services `consumer-cabys` lambda owns this table's
    schema and populates rows from the Hacienda CABYS API or the Excel import.
    cross-app-be reads from it (referenced by Product.cabys_id) and never
    writes — products link to existing rows by UUID.

    All non-PK fields are nullable from cross-app-be's perspective because
    the upstream service may insert rows before some fields are known.
    """

    __tablename__ = "cabys"

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(13), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    categories: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array as text
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    product_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tax_rate_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
