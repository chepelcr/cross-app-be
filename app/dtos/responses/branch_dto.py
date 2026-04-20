from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class BranchResponse(BaseModel):
    """Branch response DTO with snake_case fields as per design specification."""
    
    branch_id: str
    organization_id: str
    name: str
    code: str
    type: str  # 'stand' | 'restaurant'
    is_active: bool
    address: Optional[str] = None
    phone: Optional[str] = None
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    created_by: str  # user_id

    class Config:
        from_attributes = True


class BranchListResponse(BaseModel):
    """List of branches with pagination."""
    
    data: List[BranchResponse]
    pagination: PaginationResponse
