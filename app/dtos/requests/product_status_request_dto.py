"""Product Status Request DTO - Update product status."""

from pydantic import BaseModel, Field, field_validator

from app.enums.product_status import ProductStatus


class ProductStatusRequestDTO(BaseModel):
    """Product status update request."""
    
    status: int = Field(
        ...,
        description="Product status (1=Active, 2=Inactive, 3=Deleted)",
        ge=1,
        le=3,
        examples=[1, 2]
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: int) -> int:
        """Validate that status is a valid ProductStatus value."""
        if not ProductStatus.is_valid(v):
            valid_statuses = ProductStatus.get_valid_statuses()
            raise ValueError(
                f"Invalid status value: {v}. Must be one of {valid_statuses} "
                f"(1=Active, 2=Inactive, 3=Deleted)"
            )
        return v
