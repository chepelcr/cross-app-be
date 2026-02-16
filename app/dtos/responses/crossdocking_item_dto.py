"""Crossdocking Item DTO - Item in a crossdocking sale point."""

from pydantic import BaseModel, Field, ConfigDict


class CrossDockingItemDTO(BaseModel):
    """Crossdocking item."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    internal_code: str = Field(..., description="Internal product code")
    original_code: str = Field(..., description="Original product code")
    description: str = Field(..., description="Product description")
    quantity: int = Field(..., description="Quantity ordered")
    units_per_box: int = Field(..., description="Units per box")
    total_units: int = Field(..., description="Total units")
    sent: int = Field(..., description="Quantity sent")
    missing: int = Field(..., description="Quantity missing")
