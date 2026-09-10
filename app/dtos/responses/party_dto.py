"""Party DTO - Client/Supplier information."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PartyIdentificationDTO(BaseModel):
    """A party's tax identification (cédula física / jurídica / DIMEX / NITE).

    Carried on the order because billing it later needs it twice over: it is
    the receiver's identification on the electronic document, and it is what
    decides whether the customer is a retail chain with extra requirements
    (see `fe/pos-system/src/lib/chainClients.ts` — the match is on the number,
    never on the name).
    """

    model_config = ConfigDict(populate_by_name=True)

    code: Optional[str] = Field(
        None,
        description="Hacienda identification type code",
        examples=["01", "02"],
    )
    number: Optional[str] = Field(
        None,
        description="Identification number, digits only",
        examples=["3102007223"],
    )


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

    identification: Optional[PartyIdentificationDTO] = Field(
        None,
        description="Party tax identification",
    )
