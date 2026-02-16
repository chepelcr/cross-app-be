from typing import List, Optional

from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class Confirmation(Base, AuditMixin):
    __tablename__ = "crossdocking_confirmations"

    confirmation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmation_number: Mapped[str] = mapped_column(String(100), nullable=False)
    delivery_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    deliver_to_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deliver_to_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    confirmation_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="processing")

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        back_populates="confirmation"
    )

    __table_args__ = (
        Index("idx_confirmation_company_number", "company_id", "confirmation_number", unique=True),
        Index("idx_confirmation_company_id", "company_id"),
    )
