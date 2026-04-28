from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.dtos.responses.pagination_dto import PaginationResponse


class SessionResponse(BaseModel):
    """Session response DTO."""

    session_id: str
    organization_id: str
    branch_id: Optional[str] = None
    name: str
    type: str  # 'match' or 'shift'
    context: str  # 'gradas', 'mesa', or 'caja'
    start_time: str  # ISO timestamp
    end_time: Optional[str] = None  # ISO timestamp
    status: int  # 1=Active 2=Inactive 3=Deleted
    expected_revenue: Optional[float] = None
    actual_revenue: Optional[float] = None
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    created_by: str
    product_ids: Optional[List[str]] = None  # List of product IDs in this session

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """List of sessions with pagination."""

    data: List[SessionResponse]
    pagination: PaginationResponse
