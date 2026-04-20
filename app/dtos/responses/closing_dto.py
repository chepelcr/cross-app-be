from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class ClosingResponse(BaseModel):
    """Closing response DTO with snake_case fields as per design specification."""
    
    closing_id: str
    organization_id: str
    session_id: str
    assignment_id: str
    branch_id: str
    terminal_id: Optional[str] = None
    cashier_id: str
    
    # Expected amounts (from system)
    expected_cash: float
    expected_sinpe: float
    expected_card: float
    expected_total: float
    
    # Declared amounts (from cashier)
    declared_cash: float
    declared_sinpe: float
    declared_card: float
    declared_total: float
    
    # Differences (calculated)
    cash_difference: float
    sinpe_difference: float
    card_difference: float
    total_difference: float
    
    notes: Optional[str] = None
    status: str  # 'pending', 'approved', 'rejected'
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None  # ISO timestamp
    created_at: str  # ISO timestamp

    class Config:
        from_attributes = True


class ClosingListResponse(BaseModel):
    """List of closings with pagination."""
    
    data: List[ClosingResponse]
    pagination: PaginationResponse
