"""Party DTO - Client/Supplier information."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PartyDTO(BaseModel):
    """
    Party information (Client/Supplier).
    
    Represents a business party with identification and contact details.
    """
    
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = Field(
        None,
        description="Party name",
        examples=["Acme Corp", "Supplier Inc"]
    )
    
    gln: Optional[str] = Field(
        None,
        description="Global Location Number",
        examples=["1234567890123"]
    )
    
    internal_code: Optional[str] = Field(
        None,
        description="Internal party code",
        examples=["SUP-001", "CLI-456"]
    )

    logo_url: Optional[str] = Field(
        None,
        description="URL to the party's logo image",
        examples=["https://cdn.example.com/logos/acme.png"]
    )
