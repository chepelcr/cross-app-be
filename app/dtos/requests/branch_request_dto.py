from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BranchCreateRequestDTO(BaseModel):
    """Request DTO for creating a branch with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    type: Literal['stand', 'restaurant'] = Field(...)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)

    @field_validator("name", "code")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v


class BranchUpdateRequestDTO(BaseModel):
    """Request DTO for updating a branch with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[Literal['stand', 'restaurant']] = Field(None)
    is_active: Optional[bool] = Field(None)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)

    @field_validator("name", "code")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v
