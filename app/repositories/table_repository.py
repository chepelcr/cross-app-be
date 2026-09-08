from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.table import Table

logger = logging.getLogger(__name__)


class TableRepository(DatabaseConnection):
    """Mesas and bar tabs — the same object, told apart by `is_dynamic`."""

    def __init__(self):
        super().__init__()

    def find_all_by_branch(
        self, organization_id: str, branch_id: uuid.UUID, include_dynamic: bool = True
    ) -> List[Table]:
        try:
            conditions = [
                Table.organization_id == organization_id,
                Table.branch_id == branch_id,
                Table.deleted_on.is_(None),
            ]
            if not include_dynamic:
                conditions.append(Table.is_dynamic.is_(False))

            stmt = (
                select(Table)
                .where(and_(*conditions))
                # Static floor plan first, then open tabs — a cashier scans the
                # room before the tab list.
                .order_by(Table.is_dynamic, Table.sort_order, Table.code)
            )
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error finding tables for branch {branch_id}: {e}", exc_info=True)
            raise

    def find_by_id_and_organization(
        self, table_id: uuid.UUID, organization_id: str
    ) -> Optional[Table]:
        try:
            stmt = select(Table).where(
                and_(
                    Table.table_id == table_id,
                    Table.organization_id == organization_id,
                    Table.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding table {table_id}: {e}", exc_info=True)
            raise

    def find_by_branch_and_code(
        self, branch_id: uuid.UUID, code: str
    ) -> Optional[Table]:
        try:
            stmt = select(Table).where(
                and_(
                    Table.branch_id == branch_id,
                    Table.code == code,
                    Table.deleted_on.is_(None),
                )
            )
            return self.session.execute(stmt).scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error finding table by code {code}: {e}", exc_info=True)
            raise

    def save(self, table: Table) -> Table:
        try:
            self.session.add(table)
            self.session.flush()
            self.session.refresh(table)
            return table
        except SQLAlchemyError as e:
            logger.error(f"Error saving table: {e}", exc_info=True)
            raise

    def soft_delete(self, table: Table) -> None:
        """Soft-delete a static table; a closed tab is removed the same way.

        Never a hard delete: an order may still reference the table it was
        taken at, and losing that link would break the receipt.
        """
        from datetime import datetime, timezone

        try:
            table.deleted_on = datetime.now(timezone.utc)
            table.status = 0
            self.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting table {table.table_id}: {e}", exc_info=True)
            raise
