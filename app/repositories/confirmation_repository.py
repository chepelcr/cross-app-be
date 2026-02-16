from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.configuration.database_connection import DatabaseConnection
from app.models.confirmation import Confirmation
from app.models.order import Order

logger = logging.getLogger(__name__)


class ConfirmationRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, confirmation_id: int) -> Optional[Confirmation]:
        try:
            stmt = (
                select(Confirmation)
                .options(joinedload(Confirmation.orders))
                .where(
                    and_(
                        Confirmation.confirmation_id == confirmation_id,
                        Confirmation.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding confirmation {confirmation_id}: {e}", exc_info=True)
            raise

    def find_by_company_and_number(
        self, company_id: str, confirmation_number: str
    ) -> Optional[Confirmation]:
        try:
            stmt = (
                select(Confirmation)
                .options(joinedload(Confirmation.orders))
                .where(
                    and_(
                        Confirmation.company_id == company_id,
                        Confirmation.confirmation_number == confirmation_number,
                        Confirmation.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).unique().scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding confirmation {confirmation_number} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_company(
        self,
        company_id: str,
        page: int = 1,
        page_size: int = 12,
    ) -> tuple[List[Confirmation], int]:
        try:
            base_filter = and_(
                Confirmation.company_id == company_id,
                Confirmation.status == 1,
            )

            count_stmt = select(func.count()).select_from(Confirmation).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            stmt = (
                select(Confirmation)
                .options(joinedload(Confirmation.orders))
                .where(base_filter)
                .order_by(Confirmation.created_on.desc())
            )

            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            confirmations = list(self.session.execute(stmt).unique().scalars().all())
            return confirmations, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding confirmations for company {company_id}: {e}", exc_info=True
            )
            raise

    def save(self, confirmation: Confirmation) -> Confirmation:
        try:
            confirmation = self.session.merge(confirmation)
            self.session.flush()
            return confirmation
        except SQLAlchemyError as e:
            logger.error(f"Error saving confirmation: {e}", exc_info=True)
            raise
