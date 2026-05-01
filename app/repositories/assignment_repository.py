from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.assignment import Assignment

logger = logging.getLogger(__name__)


class AssignmentRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_organization(
        self, assignment_id: str, organization_id: str
    ) -> Optional[Assignment]:
        """Find an assignment by ID and organization."""
        try:
            stmt = select(Assignment).where(
                and_(
                    Assignment.assignment_id == uuid.UUID(assignment_id),
                    Assignment.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding assignment {assignment_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_organization(
        self,
        organization_id: str,
        status: Optional[int] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        branch_id: Optional[str] = None,
    ) -> List[Assignment]:
        """Find all assignments for an organization with optional filters.
        
        Args:
            organization_id: Organization UUID
            status: Filter by status (1=Active, 2=Inactive, 3=Deleted)
            session_id: Filter by session UUID
            user_id: Filter by user ID
            branch_id: Filter by branch UUID
        """
        try:
            filters = [Assignment.organization_id == organization_id]

            if status is not None:
                filters.append(Assignment.status == status)

            if session_id is not None:
                filters.append(Assignment.session_id == uuid.UUID(session_id))

            if user_id is not None:
                filters.append(Assignment.user_id == user_id)

            if branch_id is not None:
                filters.append(Assignment.branch_id == uuid.UUID(branch_id))

            stmt = select(Assignment).where(and_(*filters)).order_by(Assignment.start_time.desc())

            assignments = list(self.session.execute(stmt).scalars().all())
            return assignments
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding assignments for organization {organization_id}: {e}",
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
    ) -> Tuple[List[Assignment], int]:
        """Find assignments for an organization with pagination."""
        try:
            base = [
                Assignment.organization_id == organization_id,
                Assignment.deleted_on.is_(None),
            ]
            if filters:
                base.extend(filters)
            stmt = select(Assignment).where(and_(*base))
            total = self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar() or 0
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            else:
                stmt = stmt.order_by(Assignment.start_time.desc())
            items = list(
                self.session.execute(
                    stmt.offset((page - 1) * page_size).limit(page_size)
                ).scalars().all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding paginated assignments for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_active_assignment_for_user(self, user_id: str) -> Optional[Assignment]:
        """Find active assignment for a user (user can only have one active assignment)."""
        try:
            stmt = select(Assignment).where(
                and_(
                    Assignment.user_id == user_id,
                    Assignment.status == 1,  # Active
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding active assignment for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, assignment: Assignment) -> Assignment:
        """Save or update an assignment."""
        try:
            assignment = self.session.merge(assignment)
            self.session.flush()
            return assignment
        except SQLAlchemyError as e:
            logger.error(f"Error saving assignment: {e}", exc_info=True)
            raise

    def delete(self, assignment_id: str) -> bool:
        """Delete an assignment by ID."""
        try:
            stmt = select(Assignment).where(Assignment.assignment_id == uuid.UUID(assignment_id))
            assignment = self.session.execute(stmt).scalar_one_or_none()
            if not assignment:
                return False
            self.session.delete(assignment)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting assignment {assignment_id}: {e}", exc_info=True)
            raise

    def validate_session_exists_and_active(self, session_id: str, organization_id: str) -> bool:
        """Check if a session exists, belongs to the organization, and is active."""
        try:
            from app.models.session import Session

            stmt = select(func.count()).select_from(Session).where(
                and_(
                    Session.session_id == uuid.UUID(session_id),
                    Session.organization_id == organization_id,
                    Session.status == 1,  # Active
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error validating session {session_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
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

    def validate_terminal_exists(self, terminal_id: str, branch_id: str) -> bool:
        """Check if a terminal exists and belongs to the branch."""
        try:
            from app.models.terminal import Terminal

            stmt = select(func.count()).select_from(Terminal).where(
                and_(
                    Terminal.terminal_id == uuid.UUID(terminal_id),
                    Terminal.branch_id == uuid.UUID(branch_id),
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error validating terminal {terminal_id} for branch {branch_id}: {e}",
                exc_info=True,
            )
            raise
