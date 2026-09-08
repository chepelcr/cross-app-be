from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LinkOrderInvoiceDTO(BaseModel):
    """The electronic document that billed an order.

    Only `sale_id` is required: the rest is the Hacienda identity of the
    document, which the POS knows once it is issued and which the order badge
    renders ("Facturado · {consecutivo}").
    """

    model_config = ConfigDict(populate_by_name=True)

    sale_id: str = Field(..., min_length=1, max_length=255)
    document_type: Optional[str] = Field(None, max_length=8)
    consecutive_number: Optional[str] = Field(None, max_length=50)
    document_key: Optional[str] = Field(None, max_length=100)
    issued_on: Optional[str] = Field(None, max_length=30)
