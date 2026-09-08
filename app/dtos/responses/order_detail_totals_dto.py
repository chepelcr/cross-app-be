"""Order Detail Totals DTO - Summary totals for order details."""

from pydantic import BaseModel, Field


class OrderDetailTotals(BaseModel):
    """
    Order detail totals.
    
    Aggregated totals for all line items in an order including
    quantities ordered, dispatched, received, and financial total.
    """
    
    total_lines: int = Field(
        ...,
        description="Total number of lines in the order",
        ge=0,
        examples=[5, 10, 25]
    )
    
    total_quantity_ordered: int = Field(
        ...,
        description="Total quantity ordered across all lines (in boxes)",
        ge=0,
        examples=[100, 250, 500]
    )
    
    total_units_ordered: int = Field(
        ...,
        description="Total units ordered across all lines",
        ge=0,
        examples=[1200, 6000, 12500]
    )
    
    total_quantity_dispatched: int = Field(
        ...,
        description="Total quantity dispatched across all lines (in boxes)",
        ge=0,
        examples=[100, 250, 500]
    )
    
    total_quantity_received: int = Field(
        ...,
        description="Total quantity received across all lines (in boxes)",
        ge=0,
        examples=[100, 250, 500]
    )
    
    subtotal: float = Field(
        ...,
        description="Subtotal amount",
        ge=0,
        examples=[1000.00, 5000.50, 10000.00]
    )
    
    discounts: float = Field(
        default=0,
        description="Total discount amount across all lines",
        ge=0,
        examples=[0.0, 50.00, 100.00]
    )

    taxes: float = Field(
        default=0,
        description="Total tax amount across all lines",
        ge=0,
        examples=[0.0, 123.50, 1300.00]
    )

    net_total: float = Field(
        ...,
        description="Net total (subtotal - discounts)",
        ge=0,
        examples=[950.00, 4950.50, 9900.00]
    )
    
    grand_total: float = Field(
        ...,
        description="Grand total (net_total + taxes)",
        ge=0,
        examples=[1000.00, 5000.50, 10000.00]
    )
