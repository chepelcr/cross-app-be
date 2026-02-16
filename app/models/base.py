from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=func.now()
    )
    updated_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, onupdate=func.now()
    )
    deleted_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )


class StatusMixin:
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class AuditMixin(TimestampMixin, StatusMixin):
    pass
