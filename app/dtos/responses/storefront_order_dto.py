from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StorefrontOrderCreatedResponse(BaseModel):
    """Returned after a storefront pedido is persisted.

    Carries the internal order id, the public document/tracking number the
    customer hands off to WhatsApp, and the resulting status.
    """

    model_config = {"from_attributes": True}

    order_id: int = Field(..., description="Internal order identifier")
    document_number: str = Field(..., description="Generated order document number")
    tracking_number: str = Field(..., description="Public tracking number")
    order_status: str = Field("pending", description="Order status")
    grand_total: Optional[float] = Field(None, description="Order grand total")
