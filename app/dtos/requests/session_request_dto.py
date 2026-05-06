from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssignmentCreateDTO(BaseModel):
    """DTO for creating an assignment within a session."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: str = Field(..., description="UUID of the user to assign")
    branch_id: str = Field(..., description="UUID of the branch/station")
    terminal_id: Optional[str] = Field(None, description="Optional UUID of the terminal")
    role: str = Field(default="cashier", description="Role: 'cashier' or 'supervisor'")
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        valid_roles = ["cashier", "supervisor"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v


class SessionCreateRequestDTO(BaseModel):
    """Request DTO for creating a session with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255, description="Session name (e.g., 'Partido vs Herediano', 'Turno Mañana')")
    type: str = Field(..., description="Session type: 'match' or 'shift'")
    context: str = Field(..., description="Session context: 'gradas', 'mesa', or 'caja'")
    branch_id: Optional[str] = Field(None, description="Optional UUID of the branch for this session")
    start_time: datetime = Field(..., description="Session start time (ISO timestamp)")
    expected_revenue: Optional[float] = Field(None, ge=0, description="Expected revenue for this session")
    product_ids: Optional[List[str]] = Field(None, description="Optional list of product IDs to include in this session")
    assignments: Optional[List[AssignmentCreateDTO]] = Field(None, description="Optional list of assignments to create with this session")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        valid_types = ["match", "shift"]
        if v not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        valid_contexts = ["gradas", "mesa", "caja"]
        if v not in valid_contexts:
            raise ValueError(f"Context must be one of: {', '.join(valid_contexts)}")
        return v


class SessionUpdateRequestDTO(BaseModel):
    """Request DTO for updating a session with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, description="Session type: 'match' or 'shift'")
    context: Optional[str] = Field(None, description="Session context: 'gradas', 'mesa', or 'caja'")
    branch_id: Optional[str] = Field(None, description="UUID of the branch for this session")
    end_time: Optional[datetime] = Field(None, description="Session end time (ISO timestamp)")
    expected_revenue: Optional[float] = Field(None, ge=0)
    actual_revenue: Optional[float] = Field(None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is not None:
            valid_types = ["match", "shift"]
            if v not in valid_types:
                raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        if v is not None:
            valid_contexts = ["gradas", "mesa", "caja"]
            if v not in valid_contexts:
                raise ValueError(f"Context must be one of: {', '.join(valid_contexts)}")
        return v
