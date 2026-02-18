from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.category import Category

logger = logging.getLogger(__name__)


class CategoryRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_company(self, category_id: str, company_id: str) -> Optional[Category]:
        try:
            stmt = (
                select(Category)
                .where(
                    and_(
                        Category.id == category_id,
                        Category.organization_id == company_id,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding category {category_id} for company {company_id}: {e}", exc_info=True)
            raise

    def find_by_slug_and_company(self, slug: str, company_id: str) -> Optional[Category]:
        try:
            stmt = (
                select(Category)
                .where(
                    and_(
                        Category.slug == slug,
                        Category.organization_id == company_id,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding category by slug {slug} for company {company_id}: {e}", exc_info=True)
            raise

    def find_all_by_company(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Category], int]:
        try:
            base_filter = Category.organization_id == company_id

            # Count total
            count_stmt = select(func.count()).select_from(Category).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = select(Category).where(base_filter).order_by(Category.sort_order)

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            categories = list(self.session.execute(stmt).scalars().all())
            return categories, total
        except SQLAlchemyError as e:
            logger.error(f"Error finding categories for company {company_id}: {e}", exc_info=True)
            raise

    def save(self, category: Category) -> Category:
        try:
            category = self.session.merge(category)
            self.session.flush()
            return category
        except SQLAlchemyError as e:
            logger.error(f"Error saving category: {e}", exc_info=True)
            raise

    def delete(self, category_id: str) -> bool:
        try:
            stmt = select(Category).where(Category.id == category_id)
            category = self.session.execute(stmt).scalar_one_or_none()
            if not category:
                return False
            self.session.delete(category)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting category {category_id}: {e}", exc_info=True)
            raise
