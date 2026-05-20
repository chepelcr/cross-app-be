from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.files import ImageDTO


# ---------------------------------------------------------------------------
# Fiscal / Hacienda e-invoicing nested DTOs (input only — no computed fields)
# ---------------------------------------------------------------------------

class TaxRateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None)
    percentage: float = Field(...)


class TaxFactorDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(...)
    factor: float = Field(...)


class TaxAmountDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(...)
    amount: float = Field(...)


class TaxSpecialFieldsDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quantity: Optional[float] = Field(None)
    percentage: Optional[float] = Field(None)
    proportion: Optional[float] = Field(None)
    volume_consumption: Optional[float] = Field(None)
    tax_amount: Optional[TaxAmountDTO] = Field(None)


class ProductCodeDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_type_id: str = Field(...)
    number: str = Field(...)
    description: Optional[str] = Field(None)


class ProductDiscountDTO(BaseModel):
    """Discount input. `amount` is None on inbound requests — the BE calc sets
    it before persistence so the JSONB row carries the computed value.
    """

    model_config = ConfigDict(populate_by_name=True)

    discount_type_id: str = Field(...)
    percentage: Optional[float] = Field(None)
    reason: Optional[str] = Field(None)
    is_amount: Optional[bool] = Field(None)
    amount: Optional[float] = Field(None)


class ProductTaxDTO(BaseModel):
    """Tax input. `amount` is None on inbound requests — the BE calc sets it
    before persistence so the JSONB row carries the computed value.
    """

    model_config = ConfigDict(populate_by_name=True)

    tax_type_id: str = Field(...)
    tax_rate: Optional[TaxRateDTO] = Field(None)
    tax_factor: Optional[TaxFactorDTO] = Field(None)
    other_tax_type: Optional[str] = Field(None)
    special_fields: Optional[TaxSpecialFieldsDTO] = Field(None)
    is_amount: Optional[bool] = Field(None)
    amount: Optional[float] = Field(None)


# ---------------------------------------------------------------------------
# Main request DTO
# ---------------------------------------------------------------------------

class ProductRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Basic product fields
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    units_per_box: Optional[int] = Field(None)
    price: Optional[int] = Field(None)
    category_id: Optional[str] = Field(None)
    image: Optional[ImageDTO] = Field(None)

    # Inventory / catalogue fields
    stock_quantity: Optional[int] = Field(None)
    low_stock_threshold: Optional[int] = Field(None)
    track_inventory: Optional[bool] = Field(None)
    is_service: Optional[bool] = Field(None)
    type: Optional[str] = Field(None)
    on_sale: Optional[bool] = Field(None)
    original_price: Optional[int] = Field(None)
    discount: Optional[int] = Field(None)

    # CABYS reference — UUID of an existing data-services cabys row.
    # The row is guaranteed to exist because the FE's CABYS picker calls
    # data-services first, which upserts the row before returning it.
    cabys_id: Optional[str] = Field(None)
    # Hacienda unit-of-measure code (e.g. "Unid", "Sp", "kg").
    unit_measure: Optional[str] = Field(None)
    commercial_unit_measure: Optional[str] = Field(None)
    is_packaged: Optional[bool] = Field(None)
    quantity: Optional[float] = Field(None)
    unit_price: Optional[float] = Field(None)
    customs_part: Optional[str] = Field(None)
    codes: Optional[List[ProductCodeDTO]] = Field(None)
    discounts: Optional[List[ProductDiscountDTO]] = Field(None)
    taxes: Optional[List[ProductTaxDTO]] = Field(None)
    # Manual override for IVACE-07 only; not required in other scenarios
    base_amount: Optional[float] = Field(None)
    # salePrice is NEVER a request field — always computed by the backend
