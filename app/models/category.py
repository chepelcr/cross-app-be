from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Category(Base):
    """Maps to the existing BeautyMarket categories table.

    Read-only mapping so we can validate category_id on product creation
    and include category data in product GET responses.
    """
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    background_color: Mapped[str] = mapped_column(String(7), nullable=False)
    button_color: Mapped[str] = mapped_column(String(7), nullable=False)
    image_1_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_2_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
