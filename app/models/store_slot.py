from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StoreSlot(Base):
    __tablename__ = "store_slots"

    store_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    store_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    slot_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    chain: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
