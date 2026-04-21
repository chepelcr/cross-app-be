from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class CategoryResponse(BaseModel):
    category_id: str = Field(...)
    name: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Fiscal / Hacienda e-invoicing nested response models (output only)
# ---------------------------------------------------------------------------

class CabysResponse(BaseModel):
    id: str = Field(...)
    code: str = Field(...)
    name: str = Field(...)
    type: int = Field(...)

    class Config:
        populate_by_name = True


class ProductCodeResponse(BaseModel):
    code_type_id: str = Field(...)
    number: str = Field(...)
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ProductDiscountResponse(BaseModel):
    discount_type_id: str = Field(...)
    percentage: Optional[float] = Field(None)
    amount: Optional[float] = Field(None)  # backend-computed
    reason: Optional[str] = Field(None)
    is_amount: Optional[bool] = Field(None)

    class Config:
        populate_by_name = True


class TaxRateResponse(BaseModel):
    id: Optional[str] = Field(None)
    percentage: float = Field(...)

    class Config:
        populate_by_name = True


class TaxFactorResponse(BaseModel):
    id: str = Field(...)
    factor: float = Field(...)

    class Config:
        populate_by_name = True


class TaxAmountResponse(BaseModel):
    id: str = Field(...)
    amount: float = Field(...)

    class Config:
        populate_by_name = True


class TaxSpecialFieldsResponse(BaseModel):
    quantity: Optional[float] = Field(None)
    percentage: Optional[float] = Field(None)
    proportion: Optional[float] = Field(None)
    volume_consumption: Optional[float] = Field(None)
    tax_amount: Optional[TaxAmountResponse] = Field(None)

    class Config:
        populate_by_name = True


class ProductTaxResponse(BaseModel):
    tax_type_id: str = Field(...)
    amount: Optional[float] = Field(None)  # backend-computed
    tax_rate: Optional[TaxRateResponse] = Field(None)
    tax_factor: Optional[TaxFactorResponse] = Field(None)
    other_tax_type: Optional[str] = Field(None)
    special_fields: Optional[TaxSpecialFieldsResponse] = Field(None)
    is_amount: Optional[bool] = Field(None)

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Main product response
# ---------------------------------------------------------------------------

class ProductResponse(BaseModel):
    product_id: str = Field(...)
    company_id: str = Field(...)
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    units_per_box: Optional[int] = Field(None)
    price: Optional[float] = Field(None)
    image_url: Optional[str] = Field(None)
    category: Optional[CategoryResponse] = Field(None)

    # Inventory / catalogue fields
    status: int = Field(1)
    stock_quantity: int = Field(0)
    low_stock_threshold: int = Field(10)
    track_inventory: bool = Field(True)
    is_service: bool = Field(False)
    type: str = Field("product")
    on_sale: bool = Field(False)
    original_price: Optional[int] = Field(None)
    discount: Optional[int] = Field(None)
    created_on: Optional[datetime] = Field(None)
    updated_on: Optional[datetime] = Field(None)

    # Fiscal / Hacienda e-invoicing fields
    cabys: Optional[CabysResponse] = Field(None)
    unit_id: Optional[int] = Field(None)
    commercial_unit_measure: Optional[str] = Field(None)
    is_packaged: Optional[bool] = Field(None)
    quantity: Optional[float] = Field(None)
    unit_price: Optional[float] = Field(None)
    customs_part: Optional[str] = Field(None)
    codes: List[ProductCodeResponse] = Field(default_factory=list)
    discounts: List[ProductDiscountResponse] = Field(default_factory=list)
    taxes: List[ProductTaxResponse] = Field(default_factory=list)
    # backend-computed totals — never set by FE
    base_amount: Optional[float] = Field(None)
    sale_price: Optional[float] = Field(None)

    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    data: List[ProductResponse]
    pagination: PaginationResponse
