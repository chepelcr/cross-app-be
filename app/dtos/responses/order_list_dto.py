"""Order List DTO - Paginated list of orders."""

from pydantic import BaseModel, Field

from .order_response_dto import OrderResponse
from .pagination_dto import PaginationResponse


class OrderListResponse(BaseModel):
    """
    Order list response.
    
    Paginated list of orders with pagination metadata.
    Used for order listing endpoints with pagination support.
    """
    
    data: list[OrderResponse] = Field(
        default_factory=list,
        description="List of orders"
    )
    
    pagination: PaginationResponse = Field(
        ...,
        description="Pagination information"
    )
