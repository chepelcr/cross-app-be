from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# `code` lands in `branches.type`, is used as a dictionary key in the POS and shows
# up in URLs, so keep it to a slug rather than accepting arbitrary text.
CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class BranchTypeCreateRequestDTO(BaseModel):
    """Request DTO for creating a branch type."""

    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., min_length=1, max_length=50, description="Stable slug stored on branches.type; immutable once created")
    name: str = Field(..., min_length=1, max_length=255, description="Display label shown in the POS")
    icon: Optional[str] = Field(None, max_length=50, description="Icon name from the design-system icon set")
    color: Optional[str] = Field(None, max_length=50, description="CSS-var color token name (e.g. 'primary', 'info')")
    sort_order: Optional[int] = Field(None, ge=0, description="Display order in selectors; defaults to 0")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().lower()
        if not CODE_PATTERN.match(v):
            raise ValueError(
                "code must start with a letter or digit and contain only lowercase letters, digits, '-' or '_'"
            )
        return v

    @field_validator("name", "icon", "color")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v


class BranchTypeUpdateRequestDTO(BaseModel):
    """Request DTO for updating a branch type.

    `code` is intentionally absent: branches reference it by value, so renaming it
    here would orphan every branch already using the old code. Delete the type (only
    possible while unused) and create a new one if the code itself is wrong.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0)

    @field_validator("name", "icon", "color")
    @classmethod
    def validate_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v
