from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TableResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    table_id: str
    organization_id: str
    branch_id: str
    code: str
    name: Optional[str] = None
    seats: Optional[int] = None
    zone: Optional[str] = None
    sort_order: int = 0
    is_dynamic: bool = Field(
        False, description="True for a bar tab; false for the fixed floor plan"
    )
    opened_by: Optional[str] = None
    held_document_id: Optional[str] = Field(
        None, description="Document tab currently held against this table"
    )
    status: int = 1


class TableListResponse(BaseModel):
    data: List[TableResponse]
