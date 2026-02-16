"""Status Request DTO - Update order status."""

from pydantic import BaseModel, Field


class StatusRequestDTO(BaseModel):
    """Status update request."""
    
    status: int = Field(
        ...,
        description="Order status (1=pending, 2=processing, 3=shipped, 4=delivered, 5=cancelled)",
        ge=1,
        le=5,
        examples=[4, 5]
    )
