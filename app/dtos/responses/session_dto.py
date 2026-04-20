from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class SessionResponse(BaseModel):
    """Session response DTO with snake_case fields as per design specification."""
    
    session_id: str
    organization_id: str
    branch_id: Optional[str] = None
    name: str
    type: str  # 'match' or 'shift'
    context: str  # 'gradas', 'mesa', or 'caja'
    start_time: str  # ISO timestamp
    end_time: Optional[str] = None  # ISO timestamp
    is_active: bool
    expected_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    created_by: str

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of sessions with pagination."""
    
    data: List[SessionResponse]
    pagination: PaginationResponse
