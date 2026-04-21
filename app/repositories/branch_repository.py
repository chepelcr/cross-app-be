from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy import func, select, and_
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

    def find_all_paginated(
        self,
        organization_id: str,
        filters: list = None,
        order_by=None,
        page: int = 1,
        page_size: int = 12,
    ) -> Tuple[List[Branch], int]:
        """Find branches for an organization with pagination."""
        try:
            base = [
                Branch.organization_id == organization_id,
                Branch.deleted_on.is_(None),
            ]
            if filters:
                base.extend(filters)
            stmt = select(Branch).where(and_(*base))
            total = self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            ).scalar() or 0
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            else:
                stmt = stmt.order_by(Branch.name)
            items = list(
                self.session.execute(
                    stmt.offset((page - 1) * page_size).limit(page_size)
                ).scalars().all()
            )
            return items, total
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding paginated branches for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_branch_ids(self, branch_ids: List[str]) -> Dict[str, Branch]:
        """Find branches by list of IDs. Returns dict keyed by branch_id string."""
        if not branch_ids:
            return {}
        try:
            uuids = [uuid.UUID(bid) for bid in branch_ids]
            stmt = select(Branch).where(Branch.branch_id.in_(uuids))
            branches = list(self.session.execute(stmt).scalars().all())
            return {str(b.branch_id): b for b in branches}
        except SQLAlchemyError as e:
            logger.error(f"Error finding branches by ids: {e}", exc_info=True)
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
                    Terminal.status == 1,
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
