from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.client import Client

logger = logging.getLogger(__name__)


class ClientRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        try:
            stmt = (
                select(Client)
                .where(
                    and_(
                        Client.client_id == client_id,
                        Client.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding client {client_id}: {e}", exc_info=True)
            raise

    def find_by_company_and_gln(self, company_id: str, client_gln: str) -> Optional[Client]:
        try:
            stmt = (
                select(Client)
                .where(
                    and_(
                        Client.company_id == company_id,
                        Client.client_gln == client_gln,
                        Client.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding client by GLN {client_gln} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_company_and_name(self, company_id: str, client_name: str) -> Optional[Client]:
        try:
            stmt = (
                select(Client)
                .where(
                    and_(
                        Client.company_id == company_id,
                        Client.client_name == client_name,
                        Client.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding client by name {client_name} for company {company_id}: {e}",
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
    ) -> tuple[List[Client], int]:
        try:
            base_conditions = [
                Client.company_id == company_id,
                Client.status == 1,
            ]
            if search_filters:
                base_conditions.extend(search_filters)

            base_filter = and_(*base_conditions)

            # Count total
            count_stmt = select(func.count()).select_from(Client).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = select(Client).where(base_filter)

            # Apply sorting
            if order_by:
                stmt = stmt.order_by(order_by[0])
            else:
                stmt = stmt.order_by(desc(Client.created_on))

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            clients = list(self.session.execute(stmt).scalars().all())
            return clients, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding clients for company {company_id}: {e}", exc_info=True
            )
            raise

    def upsert(self, company_id: str, client_gln: str = None, client_name: str = None) -> Client:
        try:
            existing = None
            if client_gln:
                existing = self.find_by_company_and_gln(company_id, client_gln)
            if not existing and client_name:
                existing = self.find_by_company_and_name(company_id, client_name)

            if existing:
                if client_name is not None:
                    existing.client_name = client_name
                if client_gln is not None:
                    existing.client_gln = client_gln
                self.session.flush()
                return existing

            client = Client(
                company_id=company_id,
                client_name=client_name,
                client_gln=client_gln,
            )
            self.session.add(client)
            self.session.flush()
            return client
        except SQLAlchemyError as e:
            logger.error(f"Error upserting client for company {company_id}: {e}", exc_info=True)
            raise

    def save(self, client: Client) -> Client:
        try:
            client = self.session.merge(client)
            self.session.flush()
            return client
        except SQLAlchemyError as e:
            logger.error(f"Error saving client: {e}", exc_info=True)
            raise
