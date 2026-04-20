from __future__ import annotations

import logging
from typing import List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.branch import Branch

logger = logging.getLogger(__name__)


class BranchRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_organization(
        self, branch_id: str, organization_id: str
    ) -> Optional[Branch]:
        """Find a branch by ID and organization."""
        try:
            stmt = select(Branch).where(
                and_(
                    Branch.branch_id == uuid.UUID(branch_id),
                    Branch.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding branch {branch_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_code_and_organization(
        self, code: str, organization_id: str
    ) -> Optional[Branch]:
        """Find a branch by code and organization."""
        try:
            stmt = select(Branch).where(
                and_(
                    Branch.code == code,
                    Branch.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding branch by code {code} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_organization(
        self,
        organization_id: str,
        is_active: Optional[bool] = None,
        branch_type: Optional[str] = None,
    ) -> List[Branch]:
        """Find all branches for an organization with optional filters."""
        try:
            filters = [Branch.organization_id == organization_id]

            if is_active is not None:
                filters.append(Branch.is_active == is_active)

            if branch_type is not None:
                filters.append(Branch.type == branch_type)

            stmt = select(Branch).where(and_(*filters)).order_by(Branch.name)

            branches = list(self.session.execute(stmt).scalars().all())
            return branches
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding branches for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, branch: Branch) -> Branch:
        """Save or update a branch."""
        try:
            branch = self.session.merge(branch)
            self.session.flush()
            return branch
        except SQLAlchemyError as e:
            logger.error(f"Error saving branch: {e}", exc_info=True)
            raise

    def delete(self, branch_id: str) -> bool:
        """Delete a branch by ID."""
        try:
            stmt = select(Branch).where(Branch.branch_id == uuid.UUID(branch_id))
            branch = self.session.execute(stmt).scalar_one_or_none()
            if not branch:
                return False
            self.session.delete(branch)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting branch {branch_id}: {e}", exc_info=True)
            raise

    def has_active_terminals(self, branch_id: str) -> bool:
        """Check if a branch has active terminals."""
        try:
            from app.models.terminal import Terminal

            stmt = select(func.count()).select_from(Terminal).where(
                and_(
                    Terminal.branch_id == uuid.UUID(branch_id),
                    Terminal.is_active == True,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking active terminals for branch {branch_id}: {e}",
                exc_info=True,
            )
            raise

    def has_active_sessions(self, branch_id: str) -> bool:
        """Check if a branch has active sessions."""
        try:
            from app.models.session import Session

            stmt = select(func.count()).select_from(Session).where(
                and_(
                    Session.branch_id == uuid.UUID(branch_id),
                    Session.is_active == True,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking active sessions for branch {branch_id}: {e}",
                exc_info=True,
            )
            raise
