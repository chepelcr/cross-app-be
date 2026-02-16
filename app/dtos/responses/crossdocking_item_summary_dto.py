"""Crossdocking Item Summary DTO - Summary of items across sale points."""

from pydantic import BaseModel, Field, ConfigDict


class CrossDockingItemSummaryDTO(BaseModel):
    """Crossdocking item summary."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    internal_code: str = Field(..., description="Internal product code")
    original_code: str = Field(..., description="Original product code")
    description: str = Field(..., description="Product description")
    units_per_box: int = Field(..., description="Units per box")
    total_boxes: int = Field(..., description="Total boxes")
    total_units: int = Field(..., description="Total units")
