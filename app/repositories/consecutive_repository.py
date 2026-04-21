"""Consecutive repository for document sequence counters."""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select, and_, text, update
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.consecutive import Consecutive

logger = logging.getLogger(__name__)


class ConsecutiveRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_org(self, consecutive_id: str, organization_id: str) -> Optional[Consecutive]:
        try:
            stmt = select(Consecutive).where(
                and_(
                    Consecutive.consecutive_id == uuid.UUID(consecutive_id),
                    Consecutive.organization_id == organization_id,
                    Consecutive.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding consecutive {consecutive_id}: {e}", exc_info=True)
            raise

    def find_by_terminal_and_doc_type(
        self, terminal_id: str, document_type_id: int, organization_id: str
    ) -> Optional[Consecutive]:
        try:
            stmt = select(Consecutive).where(
                and_(
                    Consecutive.terminal_id == uuid.UUID(terminal_id),
                    Consecutive.document_type_id == document_type_id,
                    Consecutive.organization_id == organization_id,
                    Consecutive.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding consecutive by terminal/doc_type: {e}", exc_info=True)
            raise

    def find_all_by_terminal(self, terminal_id: str, organization_id: str) -> List[Consecutive]:
        try:
            stmt = select(Consecutive).where(
                and_(
                    Consecutive.terminal_id == uuid.UUID(terminal_id),
                    Consecutive.organization_id == organization_id,
                    Consecutive.deleted_on.is_(None),
                )
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error finding consecutives for terminal {terminal_id}: {e}", exc_info=True)
            raise

    def find_all_paginated(
        self,
        organization_id: str,
        filters: list = None,
        order_by=None,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Consecutive], int]:
        try:
            base = [
                Consecutive.organization_id == organization_id,
                Consecutive.deleted_on.is_(None),
            ]
            if filters:
                base.extend(filters)
            stmt = select(Consecutive).where(and_(*base))
            total = self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar() or 0
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            else:
                stmt = stmt.order_by(Consecutive.consecutive_id)
            items = list(
                self.session.execute(
                    stmt.offset((page - 1) * page_size).limit(page_size)
                ).scalars().all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(f"Error finding paginated consecutives: {e}", exc_info=True)
            raise

    def save(self, consecutive: Consecutive) -> Consecutive:
        try:
            consecutive = self.session.merge(consecutive)
            self.session.flush()
            return consecutive
        except SQLAlchemyError as e:
            logger.error(f"Error saving consecutive: {e}", exc_info=True)
            raise

    def increment_and_get(self, consecutive_id: str, organization_id: str) -> Optional[Consecutive]:
        """Atomically increment current_number and return the updated record."""
        try:
            stmt = (
                update(Consecutive)
                .where(
                    and_(
                        Consecutive.consecutive_id == uuid.UUID(consecutive_id),
                        Consecutive.organization_id == organization_id,
                    )
                )
                .values(current_number=Consecutive.current_number + 1)
                .returning(Consecutive)
            )
            result = self.session.execute(stmt).scalar_one_or_none()
            self.session.flush()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error incrementing consecutive {consecutive_id}: {e}", exc_info=True)
            raise

    def soft_delete(self, consecutive_id: str, organization_id: str) -> bool:
        from datetime import datetime, timezone
        try:
            consecutive = self.find_by_id_and_org(consecutive_id, organization_id)
            if not consecutive:
                return False
            consecutive.deleted_on = datetime.now(timezone.utc)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error soft-deleting consecutive {consecutive_id}: {e}", exc_info=True)
            raise
