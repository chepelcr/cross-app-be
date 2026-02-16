from typing import Optional

from pydantic import BaseModel, Field


class CreateConfirmationDTO(BaseModel):
    confirmation_number: str = Field(..., description="User-provided confirmation number")
    document_numbers: list[str] = Field(
        ...,
        description="List of order document numbers to link to this confirmation",
        min_items=1,
    )


class UpdateConfirmationDTO(BaseModel):
    document_numbers: list[str] = Field(
        ...,
        description="Additional order document numbers to link to this confirmation",
        min_items=1,
    )
