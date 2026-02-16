"""Order DTO - Main order information."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .crossdocking_data_dto import CrossDockingDataDTO
from .order_detail_line_dto import OrderDetailLineResponse
from .order_detail_totals_dto import OrderDetailTotals
from .party_dto import PartyDTO
from .location_dto import LocationDTO
from .order_attachments_dto import OrderAttachmentsDTO


class OrderResponse(BaseModel):
    """
    Order response.
    
    Represents a complete order with header information, line items,
    crossdocking data, and totals. Used for both single order retrieval
    and order list responses.
    
    Order Types:
        - Standard order
        - Crossdocking order
        - Direct delivery order
    
    Document Types:
        - Purchase order
        - Sales order
        - Transfer order
    """
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )
    
    order_id: int = Field(
        ...,
        description="Internal order identifier",
        examples=[1, 100, 5000]
    )
    
    company_id: str = Field(
        ...,
        description="Company identifier",
        examples=["COMP-001", "ABC123"]
    )
    
    document_number: str = Field(
        ...,
        description="Order document number",
        examples=["ORD-2024-001", "PO-123456"]
    )
    
    document_type: Optional[str] = Field(
        None,
        description="Document type code",
        examples=["PO", "SO", "TO"]
    )
    
    bgm011: Optional[str] = Field(
        None,
        description="BGM 011 code (EDI reference)",
        examples=["220", "231"]
    )
    
    confirmation_id: Optional[int] = Field(
        None,
        description="Confirmation group identifier",
    )

    confirmation_number: Optional[str] = Field(
        None,
        description="User-provided confirmation number",
    )

    order_type: Optional[str] = Field(
        None,
        description="Order type",
        examples=["Standard", "Crossdocking", "Direct"]
    )
    
    creation_date: Optional[str] = Field(
        None,
        description="Order creation date",
        examples=["2024-01-15", "2024-03-20"]
    )
    
    delivery_date: Optional[str] = Field(
        None,
        description="Expected delivery date",
        examples=["2024-01-20", "2024-03-25"]
    )
    
    order_status: Optional[str] = Field(
        "pending",
        description="Order status (pending, processing, shipped, delivered, cancelled)",
        examples=["pending", "processing", "shipped", "delivered", "cancelled"]
    )
    
    client: Optional[PartyDTO] = Field(
        None,
        description="Client information"
    )
    
    supplier: Optional[PartyDTO] = Field(
        None,
        description="Supplier information"
    )
    
    delivery_location: Optional[LocationDTO] = Field(
        None,
        description="Delivery location information"
    )
    
    event: Optional[str] = Field(
        None,
        description="Event identifier",
        examples=["EVENT-001", "PROMO-2024"]
    )
    
    department: Optional[str] = Field(
        None,
        description="Department",
        examples=["Sales", "Warehouse", "Logistics"]
    )
    
    comment: Optional[str] = Field(
        None,
        description="Additional comments",
        examples=["Urgent delivery", "Handle with care"]
    )
    
    line_count: Optional[int] = Field(
        0,
        description="Number of line items",
        ge=0,
        examples=[5, 10, 25]
    )
    
    total_quantities: Optional[int] = Field(
        0,
        description="Total quantities (boxes)",
        ge=0,
        examples=[10, 50, 100]
    )
    
    subtotal: Optional[float] = Field(
        0,
        description="Subtotal amount",
        ge=0,
        examples=[1000.00, 5000.00, 10000.00]
    )
    
    discounts: Optional[float] = Field(
        0,
        description="Total discounts applied",
        ge=0,
        examples=[0.0, 50.00, 100.00]
    )
    
    net_total: Optional[float] = Field(
        0,
        description="Net total (subtotal - discounts)",
        ge=0,
        examples=[950.00, 4950.00, 9900.00]
    )
    
    taxes: Optional[float] = Field(
        0,
        description="Total taxes",
        ge=0,
        examples=[0.0, 130.00, 500.00]
    )
    
    grand_total: Optional[float] = Field(
        0,
        description="Grand total (net_total + taxes)",
        ge=0,
        examples=[1000.00, 5000.00, 10000.00]
    )
    
    attachments: Optional[OrderAttachmentsDTO] = Field(
        None,
        description="Document attachments (PDF, Excel)"
    )
    
    lines: list[OrderDetailLineResponse] = Field(
        default_factory=list,
        description="Order line items"
    )
    
    order_totals: Optional[OrderDetailTotals] = Field(
        None,
        description="Order totals summary"
    )
    
    crossdocking: Optional[CrossDockingDataDTO] = Field(
        None,
        description="Crossdocking information if applicable"
    )
