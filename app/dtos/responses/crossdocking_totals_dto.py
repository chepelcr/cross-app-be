"""Crossdocking Totals DTO - Aggregated totals for crossdocking."""

from pydantic import BaseModel, Field, ConfigDict


class CrossDockingTotalsDTO(BaseModel):
    """Crossdocking totals."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    total_sale_points: int = Field(..., description="Total sale points")
    total_line_items: int = Field(..., description="Total line items")
    total_boxes: int = Field(..., description="Total boxes")
    total_units: int = Field(..., description="Total units")
