"""Location DTO - Delivery/dispatch location information."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LocationDTO(BaseModel):
    """
    Location information.
    
    Represents a physical location with code, name, and coordinates.
    """
    
    model_config = ConfigDict(populate_by_name=True)
    
    code: Optional[str] = Field(
        None,
        description="Location code",
        examples=["7422", "1001"]
    )
    
    name: Optional[str] = Field(
        None,
        description="Location name",
        examples=["CEDI COYOL", "Warehouse A"]
    )
    
    gln: Optional[str] = Field(
        None,
        description="Global Location Number",
        examples=["1234567890123"]
    )
    
    latitude: Optional[str] = Field(
        None,
        description="Latitude coordinate",
        examples=["9.9281", "10.0000"]
    )
    
    longitude: Optional[str] = Field(
        None,
        description="Longitude coordinate",
        examples=["-84.0907", "-85.0000"]
    )
