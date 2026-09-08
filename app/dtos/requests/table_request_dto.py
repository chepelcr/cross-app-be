from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TableCreateRequestDTO(BaseModel):
    """Create a mesa (floor plan) or open a bar tab (`is_dynamic=true`)."""

    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    seats: Optional[int] = Field(None, ge=0)
    #: Free label — "terraza", "barra". Every venue names its own areas.
    zone: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0)
    #: True opens a bar tab: created on the fly, removed when it is paid.
    is_dynamic: bool = False


class TableUpdateRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, max_length=100)
    seats: Optional[int] = Field(None, ge=0)
    zone: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0)
    #: Document tab currently held here. Null releases the table.
    held_document_id: Optional[str] = Field(None, max_length=255)
