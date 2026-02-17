from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Product(Base):
    """Maps to the existing BeautyMarket products table.

    Cross-docking replaces the BeautyMarket product CRUD entirely. New columns
    (internal_code, original_code, client_article_code, code, units_per_box) are
    added by our migration. Existing BeautyMarket columns are preserved.
    """
    __tablename__ = "products"

    # Existing BeautyMarket columns
    id: Mapped[str] = mapped_column(String, primary_key=True)
    organization_id: Mapped[str] = mapped_column(
        String, ForeignKey("organizations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id"), nullable=False
    )
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    track_inventory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="product")
    on_sale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    discount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # New columns added by our migration for cross-docking use
    internal_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    client_article_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    units_per_box: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=0)

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(foreign_keys=[organization_id])
    category: Mapped[Optional["Category"]] = relationship(foreign_keys=[category_id])

    __table_args__ = (
        Index("idx_product_org_internal_code", "organization_id", "internal_code", unique=True),
    )
