from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StorefrontOrderItemDTO(BaseModel):
    """A single line in a storefront pedido — references an existing product."""

    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0, description="Units ordered (must be > 0)")


class StorefrontOrderAddressDTO(BaseModel):
    """Structured Costa Rica delivery address (data-be location cascade ids)."""

    model_config = ConfigDict(populate_by_name=True)

    state_id: Optional[int] = Field(None, description="Provincia id")
    county_id: Optional[int] = Field(None, description="Cantón id")
    district_id: Optional[int] = Field(None, description="Distrito id")
    neighborhood_id: Optional[int] = Field(None, description="Barrio id")
    address: Optional[str] = Field(
        None, max_length=500, description="Dirección exacta (free text)"
    )


class CreateStorefrontOrderDTO(BaseModel):
    """Anonymous storefront pedido create payload.

    Placed by a guest visitor from a deployed storefront — no user account,
    no Client row. Builds a tracked Order with order_status='pending'.
    """

    model_config = ConfigDict(populate_by_name=True)

    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., min_length=1, max_length=50)
    delivery_method: Optional[str] = Field(
        None,
        max_length=50,
        description="Delivery method (e.g. 'delivery', 'pickup')",
    )
    address: Optional[StorefrontOrderAddressDTO] = Field(
        None, description="Structured CR delivery address"
    )
    items: List[StorefrontOrderItemDTO] = Field(..., min_length=1)
    comment: Optional[str] = Field(None, max_length=500)
