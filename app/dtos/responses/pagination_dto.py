"""Pagination DTO - Pagination information for list responses."""

from pydantic import BaseModel, Field


class PaginationResponse(BaseModel):
    """
    Pagination information.
    
    Contains pagination metadata for paginated list responses
    including current page, page size, and total counts.
    """
    
    page: int = Field(
        ...,
        description="Current page number (0-indexed)",
        ge=0,
        examples=[0, 1, 2]
    )
    
    pageSize: int = Field(
        ...,
        description="Number of items per page",
        ge=1,
        examples=[10, 20, 50]
    )
    
    totalElements: int = Field(
        ...,
        description="Total number of elements across all pages",
        ge=0,
        examples=[100, 250, 1000]
    )
    
    totalPages: int = Field(
        ...,
        description="Total number of pages",
        ge=0,
        examples=[10, 13, 20]
    )
