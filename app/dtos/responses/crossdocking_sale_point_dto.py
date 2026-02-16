"""Crossdocking Sale Point DTO - Sale point in crossdocking distribution."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .crossdocking_item_dto import CrossDockingItemDTO


class CrossDockingSalePointDTO(BaseModel):
    """Crossdocking sale point."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    store_number: str = Field(..., description="Store number")
    store_name: str = Field(..., description="Store name")
    full_name: str = Field(..., description="Full store name")
    slot_id: Optional[str] = Field(None, description="Slot identifier")
    items: list[CrossDockingItemDTO] = Field(default_factory=list, description="Items for this sale point")
    total_boxes: int = Field(..., description="Total boxes")
    total_units: int = Field(..., description="Total units")
