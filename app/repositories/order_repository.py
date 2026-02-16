from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from sqlalchemy import func, select, and_, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.configuration.database_connection import DatabaseConnection
from app.models.order import Order
from app.models.crossdocking_sale_point import CrossDockingSalePoint
from app.models.crossdocking_item import CrossDockingItem

logger = logging.getLogger(__name__)


class OrderRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, order_id: int) -> Optional[Order]:
        try:
            stmt = (
                select(Order)
                .options(
                    joinedload(Order.lines),
                    joinedload(Order.crossdocking_sale_points)
                    .joinedload(CrossDockingSalePoint.items),
                )
                .where(Order.order_id == order_id)
            )
            return self.session.execute(stmt).unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding order {order_id}: {e}", exc_info=True)
            raise

    def find_by_company_and_document(
        self, company_id: str, document_number: str
    ) -> Optional[Order]:
        try:
            stmt = (
                select(Order)
                .options(
                    joinedload(Order.lines),
                    joinedload(Order.crossdocking_sale_points)
                    .joinedload(CrossDockingSalePoint.items),
                )
                .where(
                    and_(
                        Order.company_id == company_id,
                        Order.document_number == document_number,
                        Order.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding order {document_number} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_company_and_documents(
        self, company_id: str, document_numbers: list[str]
    ) -> list[Order]:
        try:
            stmt = (
                select(Order)
                .options(
                    joinedload(Order.lines),
                    joinedload(Order.crossdocking_sale_points)
                    .joinedload(CrossDockingSalePoint.items),
                )
                .where(
                    and_(
                        Order.company_id == company_id,
                        Order.document_number.in_(document_numbers),
                        Order.status == 1,
                    )
                )
            )
            return list(self.session.execute(stmt).unique().scalars().all())
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding orders by documents for company {company_id}: {e}",
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
    ) -> tuple[List[Order], int]:
        try:
            base_conditions = [
                Order.company_id == company_id,
                Order.status == 1,
            ]
            if search_filters:
                base_conditions.extend(search_filters)

            base_filter = and_(*base_conditions)

            # Count total
            count_stmt = select(func.count()).select_from(Order).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = (
                select(Order)
                .options(
                    joinedload(Order.lines),
                    joinedload(Order.crossdocking_sale_points)
                    .joinedload(CrossDockingSalePoint.items),
                )
                .where(base_filter)
            )

            # Apply sorting
            if order_by:
                stmt = stmt.order_by(order_by[0])
            else:
                stmt = stmt.order_by(desc(Order.created_on))

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            orders = list(self.session.execute(stmt).unique().scalars().all())
            return orders, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding orders for company {company_id}: {e}", exc_info=True
            )
            raise

    def save(self, order: Order) -> Order:
        try:
            order = self.session.merge(order)
            self.session.flush()
            return order
        except SQLAlchemyError as e:
            logger.error(f"Error saving order: {e}", exc_info=True)
            raise

    def delete(self, order_id: int) -> bool:
        try:
            order = self.find_by_id(order_id)
            if order:
                self.session.delete(order)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting order {order_id}: {e}", exc_info=True)
            raise
