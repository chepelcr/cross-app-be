from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse

if TYPE_CHECKING:
    from app.dtos.responses.terminal_dto import TerminalResponse


class BranchResponse(BaseModel):
    """Branch response DTO."""

    branch_id: str
    organization_id: str
    name: str
    code: str
    type: str  # 'stand' | 'restaurant'
    status: int  # 1=Active 2=Inactive 3=Deleted
    address: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    created_by: str  # user_id
    terminals: List[TerminalResponse] = []

    model_config = {"from_attributes": True}


class BranchListResponse(BaseModel):
    """List of branches with pagination."""

    data: List[BranchResponse]
    pagination: PaginationResponse
