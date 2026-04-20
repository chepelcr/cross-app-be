from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from decimal import Decimal

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection
from app.models.closing import Closing

logger = logging.getLogger(__name__)


class ClosingRepository(DatabaseConnection):

    def __init__(self):
        super().__init__()

    def find_by_id_and_organization(
        self, closing_id: str, organization_id: str
    ) -> Optional[Closing]:
        """Find a closing by ID and organization."""
        try:
            stmt = select(Closing).where(
                and_(
                    Closing.closing_id == uuid.UUID(closing_id),
                    Closing.organization_id == organization_id,
                )
            )
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding closing {closing_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_all_by_organization(
        self,
        organization_id: str,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        branch_id: Optional[str] = None,
    ) -> List[Closing]:
        """Find all closings for an organization with optional filters."""
        try:
            filters = [Closing.organization_id == organization_id]

            if session_id is not None:
                filters.append(Closing.session_id == uuid.UUID(session_id))

            if status is not None:
                filters.append(Closing.status == status)

            if branch_id is not None:
                filters.append(Closing.branch_id == uuid.UUID(branch_id))

            stmt = select(Closing).where(and_(*filters)).order_by(Closing.created_at.desc())

            closings = list(self.session.execute(stmt).scalars().all())
            return closings
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding closings for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def find_by_assignment(self, assignment_id: str) -> Optional[Closing]:
        """Find a closing by assignment ID (one closing per assignment)."""
        try:
            stmt = select(Closing).where(Closing.assignment_id == uuid.UUID(assignment_id))
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error finding closing for assignment {assignment_id}: {e}",
                exc_info=True,
            )
            raise

    def save(self, closing: Closing) -> Closing:
        """Save or update a closing."""
        try:
            closing = self.session.merge(closing)
            self.session.flush()
            return closing
        except SQLAlchemyError as e:
            logger.error(f"Error saving closing: {e}", exc_info=True)
            raise

    def delete(self, closing_id: str) -> bool:
        """Delete a closing by ID."""
        try:
            stmt = select(Closing).where(Closing.closing_id == uuid.UUID(closing_id))
            closing = self.session.execute(stmt).scalar_one_or_none()
            if not closing:
                return False
            self.session.delete(closing)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting closing {closing_id}: {e}", exc_info=True)
            raise

    def validate_assignment_exists(self, assignment_id: str, organization_id: str) -> bool:
        """Check if an assignment exists and belongs to the organization."""
        try:
            from app.models.assignment import Assignment

            stmt = select(func.count()).select_from(Assignment).where(
                and_(
                    Assignment.assignment_id == uuid.UUID(assignment_id),
                    Assignment.organization_id == organization_id,
                )
            )
            count = self.session.execute(stmt).scalar() or 0
            return count > 0
        except SQLAlchemyError as e:
            logger.error(
                f"Error validating assignment {assignment_id} for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def get_assignment_details(self, assignment_id: str):
        """Get assignment details including session, branch, terminal, and cashier."""
        try:
            from app.models.assignment import Assignment

            stmt = select(Assignment).where(Assignment.assignment_id == uuid.UUID(assignment_id))
            return self.session.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting assignment details for {assignment_id}: {e}",
                exc_info=True,
            )
            raise

    def calculate_expected_amounts(self, assignment_id: str) -> dict:
        """Calculate expected amounts from orders for an assignment.
        
        NOTE: This assumes a sales_orders table exists with columns:
        - assignment_id (UUID)
        - payment_method (string: 'cash', 'sinpe', 'card')
        - total (decimal)
        
        If the table doesn't exist yet, this will return zeros.
        """
        try:
            # Check if sales_orders table exists
            # For now, we'll use a raw SQL query to handle the case where the table might not exist
            from sqlalchemy import text
            
            query = text("""
                SELECT 
                    COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total ELSE 0 END), 0) as cash,
                    COALESCE(SUM(CASE WHEN payment_method = 'sinpe' THEN total ELSE 0 END), 0) as sinpe,
                    COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total ELSE 0 END), 0) as card,
                    COALESCE(SUM(total), 0) as total
                FROM sales_orders
                WHERE assignment_id = :assignment_id
            """)
            
            result = self.session.execute(query, {"assignment_id": str(assignment_id)}).one()

            return {
                'expected_cash': Decimal(str(result.cash)),
                'expected_sinpe': Decimal(str(result.sinpe)),
                'expected_card': Decimal(str(result.card)),
                'expected_total': Decimal(str(result.total)),
            }
        except Exception as e:
            # If the table doesn't exist or there's an error, log it and return zeros
            logger.warning(
                f"Could not calculate expected amounts for assignment {assignment_id}: {e}. "
                f"Returning zeros. This is expected if sales_orders table doesn't exist yet."
            )
            return {
                'expected_cash': Decimal('0'),
                'expected_sinpe': Decimal('0'),
                'expected_card': Decimal('0'),
                'expected_total': Decimal('0'),
            }
