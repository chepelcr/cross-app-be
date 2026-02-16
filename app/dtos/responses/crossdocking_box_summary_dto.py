"""Crossdocking Box Summary DTO - Summary of boxes by item count."""

from pydantic import BaseModel, Field, ConfigDict


class CrossDockingBoxSummaryDTO(BaseModel):
    """Crossdocking box summary."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    items_per_box: int = Field(..., description="Items per box")
    box_count: int = Field(..., description="Box count")
    total_boxes: int = Field(..., description="Total boxes")
    total_units: int = Field(..., description="Total units")
