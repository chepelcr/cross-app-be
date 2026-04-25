from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class LocationResponse(BaseModel):
    """Nested location object for branch address data."""

    state_id: Optional[int] = None
    county_id: Optional[int] = None
    district_id: Optional[int] = None
    neighborhood: Optional[str] = None
    address: Optional[str] = None

    class Config:
        populate_by_name = True


class BranchResponse(BaseModel):
    """Branch response DTO."""

    branch_id: str
    organization_id: str
    name: str
    code: str
    type: str  # 'stand' | 'restaurant'
    status: int  # 1=Active 2=Inactive 3=Deleted
    location: Optional[LocationResponse] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    created_by: str  # user_id
    terminals: List["TerminalResponse"] = []  # Forward reference as string

    model_config = {"from_attributes": True}


class BranchListResponse(BaseModel):
    """List of branches with pagination."""

    data: List[BranchResponse]
    pagination: PaginationResponse


# Import at the end to avoid circular imports
from app.dtos.responses.terminal_dto import TerminalResponse
BranchResponse.model_rebuild()  # Rebuild model with actual TerminalResponse
