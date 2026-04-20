from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class TerminalResponse(BaseModel):
    """Terminal response DTO with snake_case fields as per design specification."""
    
    terminal_id: str
    organization_id: str
    branch_id: str
    name: str
    code: str
    device_id: Optional[str] = None
    is_active: bool
    registered_at: str  # ISO timestamp
    last_seen_at: Optional[str] = None  # ISO timestamp
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp

    class Config:
        from_attributes = True


class TerminalListResponse(BaseModel):
    """List of terminals with pagination."""
    
    data: List[TerminalResponse]
    pagination: PaginationResponse
