from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class AssignmentResponse(BaseModel):
    """Assignment response DTO with snake_case fields as per design specification."""
    
    assignment_id: str
    organization_id: str
    session_id: str
    user_id: str  # Cashier user_id
    branch_id: str
    terminal_id: Optional[str] = None
    role: str  # 'cashier' or 'supervisor'
    start_time: str  # ISO timestamp
    end_time: Optional[str] = None  # ISO timestamp (null if active)
    is_active: bool
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    created_by: str  # Manager user_id

    class Config:
        from_attributes = True


class AssignmentListResponse(BaseModel):
    """List of assignments with pagination."""
    
    data: List[AssignmentResponse]
    pagination: PaginationResponse
