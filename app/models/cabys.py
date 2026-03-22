from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Cabys(Base):
    """CABYS catalog table for Costa Rica Hacienda e-invoicing.

    This is a reference/catalog table — it does not use AuditMixin because
    it is not a transactional entity.
    """

    __tablename__ = "cabys"

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=_uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(13), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_cabys_code", "code", unique=True),
    )
