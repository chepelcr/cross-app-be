from __future__ import annotations

import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.cabys import Cabys

logger = logging.getLogger(__name__)


class CabysRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_code(self, code: str) -> Optional[Cabys]:
        try:
            stmt = select(Cabys).where(Cabys.code == code)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding CABYS by code {code}: {e}", exc_info=True)
            raise

    def find_by_id(self, cabys_id: uuid.UUID) -> Optional[Cabys]:
        try:
            stmt = select(Cabys).where(Cabys.id == cabys_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error finding CABYS by id {cabys_id}: {e}", exc_info=True)
            raise

    def find_or_create(self, code: str, name: str, type_: int) -> Cabys:
        """Upsert by code — used by the service layer."""
        try:
            existing = self.find_by_code(code)
            if existing:
                return existing

            cabys = Cabys(
                id=uuid.uuid4(),
                code=code,
                name=name,
                type=type_,
            )
            self.session.add(cabys)
            self.session.flush()
            return cabys
        except SQLAlchemyError as e:
            logger.error(f"Error in find_or_create CABYS code {code}: {e}", exc_info=True)
            raise

    def save(self, cabys: Cabys) -> Cabys:
        try:
            cabys = self.session.merge(cabys)
            self.session.flush()
            return cabys
        except SQLAlchemyError as e:
            logger.error(f"Error saving CABYS: {e}", exc_info=True)
            raise
