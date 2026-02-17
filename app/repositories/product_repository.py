from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import asc, func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.category import Category
from app.models.product import Product

DEFAULT_CATEGORY_ID = "uncategorized"

logger = logging.getLogger(__name__)


class ProductRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, product_id: str) -> Optional[Product]:
        try:
            stmt = (
                select(Product)
                .where(
                    and_(
                        Product.id == product_id,
                        Product.is_active == True,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding product {product_id}: {e}", exc_info=True)
            raise

    def find_by_company_and_internal_code(self, company_id: str, internal_code: str) -> Optional[Product]:
        try:
            stmt = (
                select(Product)
                .where(
                    and_(
                        Product.organization_id == company_id,
                        Product.internal_code == internal_code,
                        Product.is_active == True,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding product by internal code {internal_code} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_company(
        self,
        company_id: str,
        search_filters: list | None = None,
        order_by: tuple | None = None,
        page: int = 1,
        page_size: int = 12,
    ) -> tuple[List[Product], int]:
        try:
            base_conditions = [
                Product.organization_id == company_id,
                Product.is_active == True,
                Product.internal_code.isnot(None),
            ]
            if search_filters:
                base_conditions.extend(search_filters)

            base_filter = and_(*base_conditions)

            # Count total
            count_stmt = select(func.count()).select_from(Product).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = select(Product).where(base_filter)

            # Apply sorting
            if order_by:
                stmt = stmt.order_by(order_by[0])
            else:
                stmt = stmt.order_by(asc(Product.internal_code))

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            products = list(self.session.execute(stmt).scalars().all())
            return products, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding products for company {company_id}: {e}", exc_info=True
            )
            raise

    def _ensure_default_category(self, company_id: str) -> str:
        """Ensure the default 'uncategorized' category exists for the org."""
        stmt = select(Category).where(Category.id == DEFAULT_CATEGORY_ID)
        existing = self.session.execute(stmt).scalar_one_or_none()
        if not existing:
            cat = Category(
                id=DEFAULT_CATEGORY_ID,
                organization_id=company_id,
                name="Sin categoría",
                slug="sin-categoria",
                description="Productos sin categoría asignada",
                background_color="#FFFFFF",
                button_color="#000000",
                is_active=True,
                sort_order=999,
            )
            self.session.add(cat)
            self.session.flush()
        return DEFAULT_CATEGORY_ID

    def upsert_by_internal_code(
        self,
        company_id: str,
        internal_code: str,
        description: str = None,
        original_code: str = None,
        client_article_code: str = None,
        code: str = None,
        units_per_box: int = None,
    ) -> Product:
        try:
            existing = self.find_by_company_and_internal_code(company_id, internal_code)

            if existing:
                if description is not None:
                    existing.description = description
                if original_code is not None:
                    existing.original_code = original_code
                if client_article_code is not None:
                    existing.client_article_code = client_article_code
                if code is not None:
                    existing.code = code
                if units_per_box is not None:
                    existing.units_per_box = units_per_box
                self.session.flush()
                return existing

            category_id = self._ensure_default_category(company_id)

            product = Product(
                id=str(uuid.uuid4()),
                organization_id=company_id,
                name=description or internal_code,
                description=description or internal_code,
                price=0,
                category_id=category_id,
                is_active=True,
                internal_code=internal_code,
                original_code=original_code,
                client_article_code=client_article_code,
                code=code,
                units_per_box=units_per_box,
            )
            self.session.add(product)
            self.session.flush()
            return product
        except SQLAlchemyError as e:
            logger.error(
                f"Error upserting product by internal code {internal_code} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, product: Product) -> Product:
        try:
            product = self.session.merge(product)
            self.session.flush()
            return product
        except SQLAlchemyError as e:
            logger.error(f"Error saving product: {e}", exc_info=True)
            raise
