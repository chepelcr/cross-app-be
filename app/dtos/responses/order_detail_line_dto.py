"""Order Detail Line DTO - Individual line item in an order."""

from typing import Optional
from pydantic import BaseModel, Field


class OrderDetailLineResponse(BaseModel):
    """
    Order detail line item.
    
    Represents a single product line in an order with quantities,
    pricing, and dispatch/receipt information.
    """
    
    line_number: int = Field(
        ...,
        description="Line number in the order",
        examples=[1, 2, 3]
    )
    
    internal_code: str = Field(
        ...,
        description="Internal product code",
        examples=["INT-001", "PROD-123"]
    )
    
    code: str = Field(
        ...,
        description="Product code",
        examples=["PROD-001", "SKU-456"]
    )
    
    client_article_code: str = Field(
        ...,
        description="Client's article code",
        examples=["CLIENT-001", "ART-789"]
    )
    
    description: str = Field(
        ...,
        description="Product description",
        examples=["Product Name", "Item Description"]
    )
    
    units_per_box: int = Field(
        ...,
        description="Number of units per box",
        ge=1,
        examples=[12, 24, 50]
    )
    
    quantity_ordered: int = Field(
        ...,
        description="Quantity ordered (in boxes)",
        ge=0,
        examples=[10, 20, 50]
    )
    
    units_ordered: int = Field(
        ...,
        description="Total units ordered",
        ge=0,
        examples=[120, 480, 2500]
    )
    
    unit_price: float = Field(
        ...,
        description="Price per unit",
        ge=0,
        examples=[10.50, 25.99, 100.00]
    )
    
    discount: float = Field(
        ...,
        description="Discount amount",
        ge=0,
        examples=[0.0, 5.50, 10.00]
    )
    
    line_total: float = Field(
        ...,
        description="Total amount for this line",
        ge=0,
        examples=[100.00, 500.50, 1000.00]
    )
    
    tax: float = Field(
        ...,
        description="Tax amount for this line",
        ge=0,
        examples=[13.00, 65.07, 130.00]
    )
    
    quantity_dispatched: int = Field(
        ...,
        description="Quantity dispatched (in boxes)",
        ge=0,
        examples=[10, 20, 50]
    )
    
    dispatch_rejection_reason: Optional[str] = Field(
        None,
        description="Reason for dispatch rejection if applicable",
        examples=["Out of stock", "Damaged goods", None]
    )
    
    quantity_received: int = Field(
        ...,
        description="Quantity received (in boxes)",
        ge=0,
        examples=[10, 20, 50]
    )
    
    article_code: str = Field(
        ...,
        description="Article code",
        examples=["ART-001", "ARTICLE-456"]
    )

    product_id: Optional[str] = Field(
        None,
        description=(
            "Catalog product this line came from. REQUIRED to rebuild a cart "
            "when billing the order later — lines are linked by product_id, "
            "never by description."
        ),
        examples=["7f3d…", None]
    )

    cabys: Optional[str] = Field(
        None,
        description=(
            "CABYS code captured with the line. Kept even though a pedido is "
            "not fiscal: fabricating one later would put the wrong tax rate on "
            "a real document."
        ),
        examples=["0161010150000", None]
    )

    net_price: Optional[float] = Field(
        None,
        description="Unit price before tax",
        ge=0,
        examples=[3500.00, None]
    )

    taxes: Optional[list] = Field(
        None,
        description="Per-line tax breakdown [{code, rate_code, rate, base, amount}]",
    )

    discounts: Optional[list] = Field(
        None,
        description="Per-line discount cascade [{code, nature, percentage, amount}]",
    )
