from __future__ import annotations

import logging
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.user import User

logger = logging.getLogger(__name__)


class UserRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_ids(self, user_ids: List[str]) -> Dict[str, User]:
        """Find users by list of IDs. Returns dict keyed by user id."""
        if not user_ids:
            return {}
        try:
            stmt = select(User).where(User.id.in_(user_ids))
            users = list(self.session.execute(stmt).scalars().all())
            return {u.id: u for u in users}
        except SQLAlchemyError as e:
            logger.error(f"Error finding users by ids: {e}", exc_info=True)
            return {}
