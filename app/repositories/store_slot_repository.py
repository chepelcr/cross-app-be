import logging
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.store_slot import StoreSlot

logger = logging.getLogger(__name__)


class StoreSlotRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_code(self, store_code: str) -> Optional[StoreSlot]:
        try:
            stmt = select(StoreSlot).where(StoreSlot.store_code == store_code)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding store slot {store_code}: {e}", exc_info=True)
            raise

    def find_all(self) -> List[StoreSlot]:
        try:
            stmt = select(StoreSlot).order_by(StoreSlot.store_code)
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logger.error(f"Error finding all store slots: {e}", exc_info=True)
            raise

    def get_slot_map(self) -> Dict[str, str]:
        """Return a dict mapping store_code -> slot_id for quick lookups."""
        try:
            slots = self.find_all()
            return {s.store_code: s.slot_id or "" for s in slots}
        except SQLAlchemyError as e:
            logger.error(f"Error building slot map: {e}", exc_info=True)
            raise

    def bulk_upsert(self, slots: List[StoreSlot]) -> int:
        """Insert or update store slots. Returns count of upserted records."""
        try:
            count = 0
            for slot in slots:
                existing = self.find_by_code(slot.store_code)
                if existing:
                    existing.store_name = slot.store_name
                    existing.slot_id = slot.slot_id
                    existing.chain = slot.chain
                else:
                    self.session.add(slot)
                count += 1
            self.session.flush()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Error bulk upserting store slots: {e}", exc_info=True)
            raise
