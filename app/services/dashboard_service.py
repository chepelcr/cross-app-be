from __future__ import annotations

import logging
from typing import Optional

from app.dtos.responses.dashboard_data_dto import (
    DashboardDataResponse,
    StandData,
    ProductRanking,
)
from app.repositories.dashboard_repository import DashboardRepository

logger = logging.getLogger(__name__)


def get_dashboard_data(
    organization_id: str,
    user_id: str,
    session_id: Optional[str] = None,
) -> DashboardDataResponse:
    """Get real-time dashboard data for an organization.
    
    This aggregates data from active sessions, assignments, and sales orders
    to provide a comprehensive view of current sales performance.
    
    Args:
        organization_id: Organization identifier
        user_id: User requesting the data (for authorization)
        session_id: Optional specific session ID to filter
        
    Returns:
        DashboardDataResponse with stands, totals, and product rankings
    """
    with DashboardRepository() as repo:
        # Step 1: Get active sessions
        sessions = repo.get_active_sessions(organization_id, session_id)
        
        if not sessions:
            # No active sessions, return empty dashboard
            return DashboardDataResponse(
                stands=[],
                total_revenue=0.0,
                total_sales=0,
                avg_ticket=0.0,
                product_ranking=[],
            )
        
        session_ids = [s["session_id"] for s in sessions]
        
        # Step 2: Get active assignments for these sessions
        assignments = repo.get_active_assignments_for_sessions(session_ids)
        
        if not assignments:
            # No active assignments, return empty dashboard
            return DashboardDataResponse(
                stands=[],
                total_revenue=0.0,
                total_sales=0,
                avg_ticket=0.0,
                product_ranking=[],
            )
        
        assignment_ids = [a["assignment_id"] for a in assignments]
        
        # Step 3: Aggregate sales by assignment
        sales_by_assignment = repo.aggregate_sales_by_assignment(assignment_ids)
        
        # Step 4: Build stands data
        stands = []
        total_revenue = 0.0
        total_sales = 0
        
        # Create a map of session_id to context for quick lookup
        session_context_map = {s["session_id"]: s["context"] for s in sessions}
        
        for assignment in assignments:
            assignment_id = assignment["assignment_id"]
            sales_data = sales_by_assignment.get(assignment_id, {
                "sales_count": 0,
                "total_revenue": 0.0,
                "cash": 0.0,
                "sinpe": 0.0,
                "card": 0.0,
                "last_sync_at": 0,
            })
            
            stand = StandData(
                id=assignment["branch_id"],
                name=assignment["branch_name"],
                cashier_name=assignment["cashier_name"],
                context=session_context_map.get(assignment["session_id"], ""),
                total_revenue=sales_data["total_revenue"],
                sales_count=sales_data["sales_count"],
                cash=sales_data["cash"],
                sinpe=sales_data["sinpe"],
                card=sales_data["card"],
                last_sync_at=sales_data["last_sync_at"],
            )
            stands.append(stand)
            
            total_revenue += sales_data["total_revenue"]
            total_sales += sales_data["sales_count"]
        
        # Step 5: Calculate average ticket
        avg_ticket = total_revenue / total_sales if total_sales > 0 else 0.0
        
        # Step 6: Get product ranking
        product_ranking_data = repo.calculate_product_ranking(session_ids, limit=10)
        product_ranking = [
            ProductRanking(
                name=p["name"],
                emoji=p["emoji"],
                units=p["units"],
                revenue=p["revenue"],
            )
            for p in product_ranking_data
        ]
        
        return DashboardDataResponse(
            stands=stands,
            total_revenue=total_revenue,
            total_sales=total_sales,
            avg_ticket=avg_ticket,
            product_ranking=product_ranking,
        )
