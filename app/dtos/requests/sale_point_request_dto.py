from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SalePointItemDTO(BaseModel):
    """One product's allocation to a sale point."""

    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(..., min_length=1)
    #: Boxes allocated. Units are DERIVED from the product's units_per_box —
    #: never sent, so the two can never disagree.
    quantity: int = Field(..., ge=0)


class SalePointCreateDTO(BaseModel):
    """Capture a cross-docking sale point by hand.

    Exists because the distribution can only be created by uploading a
    spreadsheet today. A supplier who has the figures — from an email, a portal
    or a phone call — but no Excel file simply cannot record them.

    A point either names a registered `store_id` (bringing its GLN and chain) or
    carries a free `full_name` for one the client has not registered.
    """

    model_config = ConfigDict(populate_by_name=True)

    store_id: Optional[str] = None
    full_name: Optional[str] = Field(None, max_length=250)
    items: List[SalePointItemDTO] = Field(default_factory=list)


class SalePointUpdateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: Optional[str] = Field(None, max_length=250)


class SalePointItemsDTO(BaseModel):
    """Replace a sale point's whole item set."""

    model_config = ConfigDict(populate_by_name=True)

    items: List[SalePointItemDTO] = Field(default_factory=list)
