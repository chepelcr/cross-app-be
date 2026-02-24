from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.store import Store

logger = logging.getLogger(__name__)


class StoreRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id(self, store_id: uuid.UUID) -> Optional[Store]:
        try:
            stmt = (
                select(Store)
                .where(
                    and_(
                        Store.store_id == store_id,
                        Store.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding store {store_id}: {e}", exc_info=True)
            raise

    def find_by_id_and_company(self, store_id: uuid.UUID, company_id: str) -> Optional[Store]:
        try:
            stmt = (
                select(Store)
                .where(
                    and_(
                        Store.store_id == store_id,
                        Store.company_id == company_id,
                        Store.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding store {store_id} for company {company_id}: {e}", exc_info=True)
            raise

    def find_by_client_and_code(self, client_id: uuid.UUID, store_code: str) -> Optional[Store]:
        try:
            stmt = (
                select(Store)
                .where(
                    and_(
                        Store.client_id == client_id,
                        Store.store_code == store_code,
                        Store.status == 1,
                    )
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding store by code {store_code} for client {client_id}: {e}",
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
    ) -> Tuple[List[Store], int]:
        try:
            base_conditions = [
                Store.company_id == company_id,
                Store.client_id == client_id,
                Store.status == 1,
            ]
            if search_filters:
                base_conditions.extend(search_filters)

            base_filter = and_(*base_conditions)

            # Count total
            count_stmt = select(func.count()).select_from(Store).where(base_filter)
            total = self.session.execute(count_stmt).scalar() or 0

            # Build query
            stmt = select(Store).where(base_filter)

            # Apply sorting
            if order_by:
                stmt = stmt.order_by(order_by[0])
            else:
                stmt = stmt.order_by(desc(Store.created_on))

            # Apply pagination
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            stores = list(self.session.execute(stmt).scalars().all())
            return stores, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding stores for company {company_id}, client {client_id}: {e}",
                exc_info=True,
            )
            raise

    def upsert_by_code(
        self,
        company_id: str,
        client_id: uuid.UUID,
        store_code: str,
        store_name: str = None,
        slot_id: str = None,
        chain: str = None,
        gln: str = None,
    ) -> Store:
        try:
            existing = self.find_by_client_and_code(client_id, store_code)

            if existing:
                if store_name is not None:
                    existing.store_name = store_name
                if slot_id is not None:
                    existing.slot_id = slot_id
                if chain is not None:
                    existing.chain = chain
                if gln:
                    existing.gln = gln
                self.session.flush()
                return existing

            store = Store(
                company_id=company_id,
                client_id=client_id,
                store_code=store_code,
                store_name=store_name,
                slot_id=slot_id,
                chain=chain,
                gln=gln or None,
            )
            self.session.add(store)
            self.session.flush()
            return store
        except SQLAlchemyError as e:
            logger.error(
                f"Error upserting store {store_code} for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def bulk_upsert(self, company_id: str, client_id: uuid.UUID, stores_data: list) -> int:
        try:
            count = 0
            for store_data in stores_data:
                self.upsert_by_code(
                    company_id=company_id,
                    client_id=client_id,
                    store_code=store_data["store_code"],
                    store_name=store_data.get("store_name"),
                    slot_id=store_data.get("slot_id"),
                    chain=store_data.get("chain"),
                )
                count += 1
            return count
        except SQLAlchemyError as e:
            logger.error(
                f"Error bulk upserting stores for company {company_id}: {e}",
                exc_info=True,
            )
            raise

    def get_slot_map(self, company_id: str, client_id: uuid.UUID) -> Dict[str, str]:
        try:
            stmt = (
                select(Store.store_code, Store.slot_id)
                .where(
                    and_(
                        Store.company_id == company_id,
                        Store.client_id == client_id,
                        Store.status == 1,
                        Store.slot_id.isnot(None),
                    )
                )
            )
            rows = self.session.execute(stmt).all()
            return {row.store_code: row.slot_id for row in rows}
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting slot map for company {company_id}, client {client_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, store: Store) -> Store:
        try:
            store = self.session.merge(store)
            self.session.flush()
            return store
        except SQLAlchemyError as e:
            logger.error(f"Error saving store: {e}", exc_info=True)
            raise
