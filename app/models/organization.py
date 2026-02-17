from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Organization(Base):
    """Maps to the existing BeautyMarket organizations table.

    Only includes columns we need for cross-docking. New columns (gln, internal_code,
    logo_url) are added by our migration. Existing BeautyMarket columns are mapped
    read-only so we can access them without breaking anything.
    """
    __tablename__ = "organizations"

    # Existing BeautyMarket columns (read-only mapping)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    subdomain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # New columns added by our migration for cross-docking use
    gln: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    internal_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
