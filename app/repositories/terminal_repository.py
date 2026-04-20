from __future__ import annotations

import logging
from typing import List, Optional
import uuid

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.terminal import Terminal

logger = logging.getLogger(__name__)


class TerminalRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_organization(
        self, terminal_id: str, organization_id: str
    ) -> Optional[Terminal]:
        """Find a terminal by ID and organization."""
        try:
            stmt = select(Terminal).where(
                and_(
                    Terminal.terminal_id == uuid.UUID(terminal_id),
                    Terminal.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding terminal {terminal_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_code_and_organization(
        self, code: str, organization_id: str
    ) -> Optional[Terminal]:
        """Find a terminal by code and organization."""
        try:
            stmt = select(Terminal).where(
                and_(
                    Terminal.code == code,
                    Terminal.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding terminal by code {code} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_device_id(self, device_id: str) -> Optional[Terminal]:
        """Find a terminal by device_id (globally unique)."""
        try:
            stmt = select(Terminal).where(Terminal.device_id == device_id)
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding terminal by device_id {device_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_organization(
        self,
        organization_id: str,
        is_active: Optional[bool] = None,
        branch_id: Optional[str] = None,
    ) -> List[Terminal]:
        """Find all terminals for an organization with optional filters."""
        try:
            filters = [Terminal.organization_id == organization_id]

            if is_active is not None:
                filters.append(Terminal.is_active == is_active)

            if branch_id is not None:
                filters.append(Terminal.branch_id == uuid.UUID(branch_id))

            stmt = select(Terminal).where(and_(*filters)).order_by(Terminal.name)

            terminals = list(self.session.execute(stmt).scalars().all())
            return terminals
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding terminals for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, terminal: Terminal) -> Terminal:
        """Save or update a terminal."""
        try:
            terminal = self.session.merge(terminal)
            self.session.flush()
            return terminal
        except SQLAlchemyError as e:
            logger.error(f"Error saving terminal: {e}", exc_info=True)
            raise

    def delete(self, terminal_id: str) -> bool:
        """Delete a terminal by ID."""
        try:
            stmt = select(Terminal).where(Terminal.terminal_id == uuid.UUID(terminal_id))
            terminal = self.session.execute(stmt).scalar_one_or_none()
            if not terminal:
                return False
            self.session.delete(terminal)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting terminal {terminal_id}: {e}", exc_info=True)
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

    def has_active_assignments(self, terminal_id: str) -> bool:
        """Check if a terminal has active assignments."""
        try:
            from app.models.assignment import Assignment

            stmt = select(func.count()).select_from(Assignment).where(
                and_(
                    Assignment.terminal_id == uuid.UUID(terminal_id),
                    Assignment.is_active == True,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking active assignments for terminal {terminal_id}: {e}",
                exc_info=True,
            )
            raise
