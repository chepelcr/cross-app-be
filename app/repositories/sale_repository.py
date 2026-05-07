from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.sale import Sale
from app.models.sale_line import SaleLine

logger = logging.getLogger(__name__)


class SaleRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def save(self, sale: Sale) -> Sale:
        try:
            sale = self.session.merge(sale)
            self.session.flush()
            return sale
        except SQLAlchemyError as e:
            logger.error(f"Error saving sale: {e}", exc_info=True)
            raise

    def save_lines(self, lines: List[SaleLine]) -> List[SaleLine]:
        try:
            saved = []
            for line in lines:
                saved.append(self.session.merge(line))
            self.session.flush()
            return saved
        except SQLAlchemyError as e:
            logger.error(f"Error saving sale lines: {e}", exc_info=True)
            raise

    def find_by_id_and_organization(
        self, sale_id: str, organization_id: str
    ) -> Optional[Sale]:
        try:
            stmt = select(Sale).where(
                and_(
                    Sale.sale_id == uuid.UUID(sale_id),
                    Sale.organization_id == organization_id,
                    Sale.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding sale {sale_id}: {e}", exc_info=True)
            raise

    def find_lines_by_sale(self, sale_id: str) -> List[SaleLine]:
        try:
            stmt = (
                select(SaleLine)
                .where(SaleLine.sale_id == uuid.UUID(sale_id))
                .order_by(SaleLine.line_number)
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error finding lines for sale {sale_id}: {e}", exc_info=True)
            raise

    def find_all_paginated(
        self,
        organization_id: str,
        filters: list = None,
        order_by=None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Sale], int]:
        try:
            base = [
                Sale.organization_id == organization_id,
                Sale.deleted_on.is_(None),
            ]
            if filters:
                base.extend(filters)
            stmt = select(Sale).where(and_(*base))
            total = self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar() or 0
            stmt = stmt.order_by(order_by if order_by is not None else Sale.created_on.desc())
            items = list(
                self.session.execute(
                    stmt.offset((page - 1) * page_size).limit(page_size)
                ).scalars().all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(f"Error listing sales for org {organization_id}: {e}", exc_info=True)
            raise
