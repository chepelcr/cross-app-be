from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.dtos.responses.pagination_dto import PaginationResponse


class AssignmentUserDTO(BaseModel):
    """Embedded user details for assignment responses (read from shared users table)."""

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class AssignmentProductDTO(BaseModel):
    """Lightweight product info for assignment responses."""
    
    product_id: str
    name: str
    price: float
    image_url: Optional[str] = None
    category_id: Optional[str] = None
    stock_quantity: int = 0
    track_inventory: bool = True
    status: int = 1

    model_config = {"from_attributes": True}


class AssignmentResponse(BaseModel):
    """Assignment response DTO."""

    assignment_id: str
    organization_id: str
    session_id: str
    user_id: str  # Cashier user_id
    branch_id: str
    terminal_id: Optional[str] = None
    role: str  # 'cashier' or 'supervisor'
    start_time: str  # ISO timestamp
    end_time: Optional[str] = None  # ISO timestamp (null if active)
    status: int  # 1=Active 2=Inactive 3=Deleted
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    created_by: str  # Manager user_id
    user: Optional[AssignmentUserDTO] = None  # Enriched user data from shared DB
    products: Optional[List[AssignmentProductDTO]] = None  # Products from session

    model_config = {"from_attributes": True}


class AssignmentListResponse(BaseModel):
    """List of assignments with pagination."""

    data: List[AssignmentResponse]
    pagination: PaginationResponse
