from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class StandData(BaseModel):
    """Stand data for dashboard with snake_case fields."""
    
    id: str  # branch_id
    name: str
    cashier_name: str
    context: str
    total_revenue: float
    sales_count: int
    cash: float
    sinpe: float
    card: float
    last_sync_at: int  # timestamp

    class Config:
        from_attributes = True


class ProductRanking(BaseModel):
    """Product ranking data for dashboard with snake_case fields."""
    
    name: str
    emoji: str
    units: int
    revenue: float

    class Config:
        from_attributes = True


class DashboardDataResponse(BaseModel):
    """Dashboard data response DTO with snake_case fields as per design specification.
    
    This is a computed/aggregated response, not a database model.
    """
    
    stands: List[StandData]
    total_revenue: float
    total_sales: int
    avg_ticket: float
    product_ranking: List[ProductRanking]

    class Config:
        from_attributes = True
