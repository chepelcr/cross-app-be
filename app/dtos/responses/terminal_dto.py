from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.dtos.responses.pagination_dto import PaginationResponse


class TerminalResponse(BaseModel):
    """Terminal response DTO."""

    terminal_id: str
    organization_id: str
    branch_id: str
    name: str
    code: int
    device_id: Optional[str] = None
    status: int  # 1=Active 2=Inactive 3=Deleted
    registered_at: Optional[str] = None  # ISO timestamp
    last_seen_at: Optional[str] = None  # ISO timestamp
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp

    model_config = {"from_attributes": True}


class TerminalListResponse(BaseModel):
    """List of terminals with pagination."""

    data: List[TerminalResponse]
    pagination: PaginationResponse
