from __future__ import annotations

from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClosingCreateRequestDTO(BaseModel):
    """Request DTO for creating a closing with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(..., description="UUID of the session")
    assignment_id: str = Field(..., description="UUID of the assignment")
    
    # Declared amounts (from cashier)
    declared_cash: Decimal = Field(..., ge=0, description="Declared cash amount")
    declared_sinpe: Decimal = Field(..., ge=0, description="Declared SINPE amount")
    declared_card: Decimal = Field(..., ge=0, description="Declared card amount")
    declared_total: Decimal = Field(..., ge=0, description="Declared total amount")
    
    notes: Optional[str] = Field(None, description="Optional notes from cashier")

    @field_validator("declared_cash", "declared_sinpe", "declared_card", "declared_total")
    @classmethod
    def validate_decimal_precision(cls, v):
        """Ensure decimal values have at most 2 decimal places."""
        if v is not None:
            # Check if the value has more than 2 decimal places
            if v.as_tuple().exponent < -2:
                raise ValueError("Amount cannot have more than 2 decimal places")
        return v


class ClosingUpdateRequestDTO(BaseModel):
    """Request DTO for updating a closing with snake_case fields."""
    
    model_config = ConfigDict(populate_by_name=True)

    status: Optional[Literal['pending', 'approved', 'rejected']] = Field(
        None, description="Closing status: 'pending', 'approved', or 'rejected'"
    )
    reviewed_by: Optional[str] = Field(None, description="User ID of the reviewer (manager)")
    notes: Optional[str] = Field(None, description="Optional notes")
