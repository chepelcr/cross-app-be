from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.session import Session

logger = logging.getLogger(__name__)


class SessionRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_organization(
        self, session_id: str, organization_id: str
    ) -> Optional[Session]:
        """Find a session by ID and organization."""
        try:
            stmt = select(Session).where(
                and_(
                    Session.session_id == uuid.UUID(session_id),
                    Session.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding session {session_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_organization(
        self,
        organization_id: str,
        is_active: Optional[bool] = None,
        branch_id: Optional[str] = None,
        session_type: Optional[str] = None,
        context: Optional[str] = None,
    ) -> List[Session]:
        """Find all sessions for an organization with optional filters."""
        try:
            filters = [Session.organization_id == organization_id]

            if is_active is not None:
                filters.append(Session.is_active == is_active)

            if branch_id is not None:
                filters.append(Session.branch_id == uuid.UUID(branch_id))

            if session_type is not None:
                filters.append(Session.type == session_type)

            if context is not None:
                filters.append(Session.context == context)

            stmt = select(Session).where(and_(*filters)).order_by(Session.start_time.desc())

            sessions = list(self.session.execute(stmt).scalars().all())
            return sessions
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding sessions for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_paginated(
        self,
        organization_id: str,
        filters: list = None,
        order_by=None,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Session], int]:
        """Find sessions for an organization with pagination."""
        try:
            base = [
                Session.organization_id == organization_id,
                Session.deleted_on.is_(None),
            ]
            if filters:
                base.extend(filters)
            stmt = select(Session).where(and_(*base))
            total = self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar() or 0
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            else:
                stmt = stmt.order_by(Session.start_time.desc())
            items = list(
                self.session.execute(
                    stmt.offset((page - 1) * page_size).limit(page_size)
                ).scalars().all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding paginated sessions for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, session: Session) -> Session:
        """Save or update a session."""
        try:
            session = self.session.merge(session)
            self.session.flush()
            return session
        except SQLAlchemyError as e:
            logger.error(f"Error saving session: {e}", exc_info=True)
            raise

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID."""
        try:
            stmt = select(Session).where(Session.session_id == uuid.UUID(session_id))
            session = self.session.execute(stmt).scalar_one_or_none()
            if not session:
                return False
            self.session.delete(session)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            raise

    def validate_branch_exists(self, branch_id: str, organization_id: str) -> bool:
        """Check if a branch exists and belongs to the organization."""
        try:
            from app.models.branch import Branch

            stmt = select(func.count()).select_from(Branch).where(
                and_(
                    Branch.branch_id == uuid.UUID(branch_id),
                    Branch.organization_id == organization_id,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error validating branch {branch_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def has_active_assignments(self, session_id: str) -> bool:
        """Check if a session has active assignments."""
        try:
            from app.models.assignment import Assignment

            stmt = select(func.count()).select_from(Assignment).where(
                and_(
                    Assignment.session_id == uuid.UUID(session_id),
                    Assignment.is_active == True,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking active assignments for session {session_id}: {e}",
                exc_info=True,
            )
            raise
