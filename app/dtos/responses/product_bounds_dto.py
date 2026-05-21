from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductPriceBoundsResponse(BaseModel):
    """Min/max bounds for the org's product net & sale prices.

    Surfaced for the FE filter slider so the thumbs match the organization's
    actual price range. Any side may be `None` if the org has no products
    (or no sale price set on any product) — callers should fall back to a
    sensible default in that case.
    """

    model_config = ConfigDict(populate_by_name=True)

    net_min: Optional[float] = Field(None, description="Lowest net price across non-deleted products")
    net_max: Optional[float] = Field(None, description="Highest net price across non-deleted products")
    sale_min: Optional[float] = Field(None, description="Lowest sale price across non-deleted products")
    sale_max: Optional[float] = Field(None, description="Highest sale price across non-deleted products")
