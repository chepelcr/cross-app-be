from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import FastAPI, Header, HTTPException, Path, Query

from app.dtos.responses.dashboard_data_dto import DashboardDataResponse
from app.services import dashboard_service

logger = logging.getLogger(__name__)


class DashboardController:
    """Controller for dashboard endpoints."""

    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/dashboard",
            response_model=DashboardDataResponse,
            tags=["dashboard"],
            summary="Get real-time dashboard data",
            description="""Get real-time sales dashboard data for an organization.

**Query Parameters:**
- `session_id`: Optional UUID to filter by specific session

**Response:**
Returns aggregated dashboard data including:
- `stands`: Array of stand/branch data with sales metrics
  - `id`: Branch ID
  - `name`: Branch name
  - `cashier_name`: Assigned cashier name
  - `context`: Session context (gradas/mesa/caja)
  - `total_revenue`: Total revenue for this stand
  - `sales_count`: Number of sales
  - `cash`: Cash payment total
  - `sinpe`: SINPE payment total
  - `card`: Card payment total
  - `last_sync_at`: Timestamp of last order sync
- `total_revenue`: Total revenue across all stands
- `total_sales`: Total number of sales across all stands
- `avg_ticket`: Average ticket value (total_revenue / total_sales)
- `product_ranking`: Top 10 products by revenue
  - `name`: Product name
  - `emoji`: Product image/emoji
  - `units`: Units sold
  - `revenue`: Total revenue for this product

**Logic:**
1. Gets active sessions for the organization (optionally filtered by session_id)
2. Gets active assignments for those sessions
3. Aggregates sales data from orders by assignment
4. Calculates payment method breakdowns
5. Computes product rankings
6. Calculates global KPIs (total_revenue, total_sales, avg_ticket)

**Examples:**
- Get dashboard for all active sessions: `/api/organizations/{orgId}/dashboard`
- Get dashboard for specific session: `/api/organizations/{orgId}/dashboard?session_id={sessionId}`

**Authorization:**
- User must be a member of the organization (enforced at API Gateway/auth layer)
""",
        )
        async def get_dashboard(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            session_id: Optional[str] = Query(
                None, description="Optional session UUID to filter by specific session"
            ),
        ):
            try:
                return dashboard_service.get_dashboard_data(
                    organization_id,
                    x_user_id,
                    session_id=session_id,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error getting dashboard data: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
