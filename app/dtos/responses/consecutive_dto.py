from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.dtos.responses.pagination_dto import PaginationResponse


class ConsecutiveResponse(BaseModel):
    """Consecutive (document sequence counter) response DTO."""

    consecutive_id: str
    organization_id: str
    terminal_id: str
    document_type_id: int
    current_number: int
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    created_by: str

    model_config = {"from_attributes": True}


class ConsecutiveListResponse(BaseModel):
    """List of consecutives with pagination."""

    data: List[ConsecutiveResponse]
    pagination: PaginationResponse
