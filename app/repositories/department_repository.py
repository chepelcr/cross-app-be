from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.department import Department

logger = logging.getLogger(__name__)


class DepartmentRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, department_id: uuid.UUID) -> Optional[Department]:
        try:
            stmt = (
                select(Department)
                .where(
                    and_(
                        Department.department_id == department_id,
                        Department.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding department {department_id}: {e}", exc_info=True)
            raise

    def find_by_client_and_code(self, client_id: uuid.UUID, department_code: str) -> Optional[Department]:
        try:
            stmt = (
                select(Department)
                .where(
                    and_(
                        Department.client_id == client_id,
                        Department.department_code == department_code,
                        Department.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding department by code {department_code} for client {client_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_client(
        self,
        company_id: str,
        client_id: uuid.UUID,
        search_filters: list | None = None,
        order_by: tuple | None = None,
        page: int = 1,
        page_size: int = 12,
    ) -> tuple[List[Department], int]:
        try:
            base_conditions = [
                Department.company_id == company_id,
                Department.client_id == client_id,
                Department.status == 1,
            ]
            if search_filters:
                base_conditions.extend(search_filters)

            base_filter = and_(*base_conditions)

            # Count total
            count_stmt = select(func.count()).select_from(Department).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = select(Department).where(base_filter)

            # Apply sorting
            if order_by:
                stmt = stmt.order_by(order_by[0])
            else:
                stmt = stmt.order_by(desc(Department.created_on))

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            departments = list(self.session.execute(stmt).scalars().all())
            return departments, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding departments for company {company_id}, client {client_id}: {e}",
                exc_info=True,
            )
            raise

    def upsert_by_code(
        self,
        company_id: str,
        client_id: uuid.UUID,
        department_code: str,
        name: str = None,
        supplier_code: str = None,
    ) -> Department:
        try:
            existing = self.find_by_client_and_code(client_id, department_code)

            if existing:
                if name is not None:
                    existing.name = name
                if supplier_code is not None:
                    existing.supplier_code = supplier_code
                self.session.flush()
                return existing

            department = Department(
                company_id=company_id,
                client_id=client_id,
                department_code=department_code,
                name=name,
                supplier_code=supplier_code,
            )
            self.session.add(department)
            self.session.flush()
            return department
        except SQLAlchemyError as e:
            logger.error(
                f"Error upserting department for company {company_id}, client {client_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, department: Department) -> Department:
        try:
            department = self.session.merge(department)
            self.session.flush()
            return department
        except SQLAlchemyError as e:
            logger.error(f"Error saving department: {e}", exc_info=True)
            raise

    def soft_delete(self, department_id: uuid.UUID) -> bool:
        try:
            department = self.find_by_id(department_id)
            if not department:
                return False
            department.status = 0
            department.deleted_on = datetime.now()
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error soft deleting department {department_id}: {e}", exc_info=True)
            raise
