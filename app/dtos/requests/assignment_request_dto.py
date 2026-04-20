from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentCreateRequestDTO(BaseModel):
    """Request DTO for creating an assignment with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., description="UUID of the session")
    user_id: str = Field(..., description="User ID of the cashier/supervisor")
    branch_id: str = Field(..., description="UUID of the branch")
    terminal_id: Optional[str] = Field(None, description="Optional UUID of the terminal")
    role: Literal['cashier', 'supervisor'] = Field(..., description="Role: 'cashier' or 'supervisor'")
    start_time: datetime = Field(..., description="Assignment start time (ISO timestamp)")

    @field_validator("user_id")
    @classmethod
    def validate_user_id_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("User ID cannot be empty or whitespace")
        return v


class AssignmentUpdateRequestDTO(BaseModel):
    """Request DTO for updating an assignment with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    end_time: Optional[datetime] = Field(None, description="Assignment end time (ISO timestamp)")
    is_active: Optional[bool] = Field(None, description="Whether the assignment is active")
    terminal_id: Optional[str] = Field(None, description="UUID of the terminal")
