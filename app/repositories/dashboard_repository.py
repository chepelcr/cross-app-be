from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
import uuid

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.configuration.database_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class DashboardRepository(DatabaseConnection):
    """Repository for dashboard data aggregation queries."""

    def __init__(self):
        super().__init__()

    def get_active_sessions(self, organization_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active sessions for an organization.
        
        Args:
            organization_id: Organization identifier
            session_id: Optional specific session ID to filter
            
        Returns:
            List of session dictionaries with session_id, name, type, context
        """
        try:
            if session_id:
                query = text("""
                    SELECT session_id, name, type, context
                    FROM sales_sessions
                    WHERE organization_id = :org_id 
                      AND session_id = :session_id
                      AND is_active = true
                """)
                result = self.session.execute(
                    query, 
                    {"org_id": organization_id, "session_id": session_id}
                ).fetchall()
            else:
                query = text("""
                    SELECT session_id, name, type, context
                    FROM sales_sessions
                    WHERE organization_id = :org_id 
                      AND is_active = true
                """)
                result = self.session.execute(query, {"org_id": organization_id}).fetchall()
            
            return [
                {
                    "session_id": str(row.session_id),
                    "name": row.name,
                    "type": row.type,
                    "context": row.context,
                }
                for row in result
            ]
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting active sessions for organization {organization_id}: {e}",
                exc_info=True,
            )
            raise

    def get_active_assignments_for_sessions(self, session_ids: List[str]) -> List[Dict[str, Any]]:
        """Get active assignments for given sessions with branch and cashier info.
        
        Args:
            session_ids: List of session UUIDs
            
        Returns:
            List of assignment dictionaries with assignment details
        """
        if not session_ids:
            return []
            
        try:
            # Note: We're assuming a users table exists or we'll need to handle user info differently
            # For now, we'll use user_id as cashier_name if users table doesn't exist
            query = text("""
                SELECT 
                    a.assignment_id,
                    a.session_id,
                    a.branch_id,
                    a.user_id as cashier_id,
                    a.user_id as cashier_name,
                    b.name as branch_name,
                    b.code as branch_code
                FROM assignments a
                JOIN branches b ON a.branch_id = b.branch_id
                WHERE a.session_id = ANY(:session_ids)
                  AND a.is_active = true
            """)
            
            result = self.session.execute(
                query,
                {"session_ids": session_ids}
            ).fetchall()
            
            return [
                {
                    "assignment_id": str(row.assignment_id),
                    "session_id": str(row.session_id),
                    "branch_id": str(row.branch_id),
                    "branch_name": row.branch_name,
                    "branch_code": row.branch_code,
                    "cashier_id": row.cashier_id,
                    "cashier_name": row.cashier_name,
                }
                for row in result
            ]
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting active assignments for sessions: {e}",
                exc_info=True,
            )
            raise

    def aggregate_sales_by_assignment(self, assignment_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Aggregate sales data by assignment from sales_orders table.
        
        Args:
            assignment_ids: List of assignment UUIDs
            
        Returns:
            Dictionary mapping assignment_id to sales data
        """
        if not assignment_ids:
            return {}
            
        try:
            query = text("""
                SELECT 
                    a.assignment_id,
                    COUNT(o.order_id) as sales_count,
                    COALESCE(SUM(o.total), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN o.payment_method = 'cash' THEN o.total ELSE 0 END), 0) as cash,
                    COALESCE(SUM(CASE WHEN o.payment_method = 'sinpe' THEN o.total ELSE 0 END), 0) as sinpe,
                    COALESCE(SUM(CASE WHEN o.payment_method = 'card' THEN o.total ELSE 0 END), 0) as card,
                    MAX(o.created_at) as last_sync_at
                FROM assignments a
                LEFT JOIN sales_orders o ON o.assignment_id = a.assignment_id
                WHERE a.assignment_id = ANY(:assignment_ids)
                GROUP BY a.assignment_id
            """)
            
            result = self.session.execute(
                query,
                {"assignment_ids": assignment_ids}
            ).fetchall()
            
            return {
                str(row.assignment_id): {
                    "sales_count": row.sales_count or 0,
                    "total_revenue": float(row.total_revenue or 0),
                    "cash": float(row.cash or 0),
                    "sinpe": float(row.sinpe or 0),
                    "card": float(row.card or 0),
                    "last_sync_at": int(row.last_sync_at.timestamp()) if row.last_sync_at else 0,
                }
                for row in result
            }
        except Exception as e:
            # If sales_orders table doesn't exist, return empty data
            logger.warning(
                f"Could not aggregate sales by assignment: {e}. "
                f"Returning zeros. This is expected if sales_orders table doesn't exist yet."
            )
            return {
                assignment_id: {
                    "sales_count": 0,
                    "total_revenue": 0.0,
                    "cash": 0.0,
                    "sinpe": 0.0,
                    "card": 0.0,
                    "last_sync_at": 0,
                }
                for assignment_id in assignment_ids
            }

    def calculate_product_ranking(self, session_ids: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Calculate product ranking by revenue for given sessions.
        
        Args:
            session_ids: List of session UUIDs
            limit: Maximum number of products to return (default 10)
            
        Returns:
            List of product ranking dictionaries
        """
        if not session_ids:
            return []
            
        try:
            query = text("""
                SELECT 
                    p.name,
                    p.image_url as emoji,
                    COALESCE(SUM(oi.quantity), 0) as units,
                    COALESCE(SUM(oi.quantity * oi.unit_price), 0) as revenue
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN sales_orders o ON oi.order_id = o.order_id
                WHERE o.session_id = ANY(:session_ids)
                GROUP BY p.product_id, p.name, p.image_url
                ORDER BY revenue DESC
                LIMIT :limit
            """)
            
            result = self.session.execute(
                query,
                {"session_ids": session_ids, "limit": limit}
            ).fetchall()
            
            return [
                {
                    "name": row.name,
                    "emoji": row.emoji or "",
                    "units": int(row.units or 0),
                    "revenue": float(row.revenue or 0),
                }
                for row in result
            ]
        except Exception as e:
            # If tables don't exist, return empty list
            logger.warning(
                f"Could not calculate product ranking: {e}. "
                f"Returning empty list. This is expected if sales_orders or related tables don't exist yet."
            )
            return []
