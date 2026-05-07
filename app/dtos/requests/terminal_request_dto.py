from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TerminalCreateRequestDTO(BaseModel):
    """Request DTO for creating a terminal with snake_case fields."""

    model_config = ConfigDict(populate_by_name=True)

    branch_id: Optional[str] = Field(None, description="Set by the controller from URL path")
    name: str = Field(..., min_length=1, max_length=255)
    code: int = Field(..., ge=1, description="Numeric terminal code, unique per organization (Hacienda requirement)")
    device_id: Optional[str] = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v


class TerminalUpdateRequestDTO(BaseModel):
    """Request DTO for updating a terminal with snake_case fields."""

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[int] = Field(None, ge=1)
    device_id: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None)
    branch_id: Optional[str] = Field(None, description="Set by the controller from URL path")

    @field_validator("name")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v
