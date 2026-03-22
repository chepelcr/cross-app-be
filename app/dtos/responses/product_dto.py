from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class CategoryResponse(BaseModel):
    category_id: str = Field(..., alias="categoryId")
    name: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Fiscal / Hacienda e-invoicing nested response models (output only)
# ---------------------------------------------------------------------------

class CabysResponse(BaseModel):
    id: str = Field(..., alias="id")
    code: str = Field(..., alias="code")
    name: str = Field(..., alias="name")
    type: int = Field(..., alias="type")

    class Config:
        populate_by_name = True


class ProductCodeResponse(BaseModel):
    code_type_id: str = Field(..., alias="codeTypeId")
    number: str = Field(..., alias="number")
    description: Optional[str] = Field(None, alias="description")

    class Config:
        populate_by_name = True


class ProductDiscountResponse(BaseModel):
    discount_type_id: str = Field(..., alias="discountTypeId")
    percentage: Optional[float] = Field(None, alias="percentage")
    amount: Optional[float] = Field(None, alias="amount")  # backend-computed
    reason: Optional[str] = Field(None, alias="reason")
    is_amount: Optional[bool] = Field(None, alias="isAmount")

    class Config:
        populate_by_name = True


class TaxRateResponse(BaseModel):
    id: Optional[str] = Field(None, alias="id")
    percentage: float = Field(..., alias="percentage")

    class Config:
        populate_by_name = True


class TaxFactorResponse(BaseModel):
    id: str = Field(..., alias="id")
    factor: float = Field(..., alias="factor")

    class Config:
        populate_by_name = True


class TaxAmountResponse(BaseModel):
    id: str = Field(..., alias="id")
    amount: float = Field(..., alias="amount")

    class Config:
        populate_by_name = True


class TaxSpecialFieldsResponse(BaseModel):
    quantity: Optional[float] = Field(None, alias="quantity")
    percentage: Optional[float] = Field(None, alias="percentage")
    proportion: Optional[float] = Field(None, alias="proportion")
    volume_consumption: Optional[float] = Field(None, alias="volumeConsumption")
    tax_amount: Optional[TaxAmountResponse] = Field(None, alias="taxAmount")

    class Config:
        populate_by_name = True


class ProductTaxResponse(BaseModel):
    tax_type_id: str = Field(..., alias="taxTypeId")
    amount: Optional[float] = Field(None, alias="amount")  # backend-computed
    tax_rate: Optional[TaxRateResponse] = Field(None, alias="taxRate")
    tax_factor: Optional[TaxFactorResponse] = Field(None, alias="taxFactor")
    other_tax_type: Optional[str] = Field(None, alias="otherTaxType")
    special_fields: Optional[TaxSpecialFieldsResponse] = Field(None, alias="specialFields")
    is_amount: Optional[bool] = Field(None, alias="isAmount")

    class Config:
        populate_by_name = True


# ---------------------------------------------------------------------------
# Main product response
# ---------------------------------------------------------------------------

class ProductResponse(BaseModel):
    product_id: str = Field(..., alias="productId")
    company_id: str = Field(..., alias="companyId")
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    units_per_box: Optional[int] = Field(None, alias="unitsPerBox")
    price: Optional[float] = Field(None)
    image_url: Optional[str] = Field(None, alias="imageUrl")
    category: Optional[CategoryResponse] = Field(None)

    # Fiscal / Hacienda e-invoicing fields
    cabys: Optional[CabysResponse] = Field(None, alias="cabys")
    unit_id: Optional[int] = Field(None, alias="unitId")
    commercial_unit_measure: Optional[str] = Field(None, alias="commercialUnitMeasure")
    is_packaged: Optional[bool] = Field(None, alias="isPackaged")
    quantity: Optional[float] = Field(None, alias="quantity")
    unit_price: Optional[float] = Field(None, alias="unitPrice")
    customs_part: Optional[str] = Field(None, alias="customsPart")
    codes: List[ProductCodeResponse] = Field(default_factory=list, alias="codes")
    discounts: List[ProductDiscountResponse] = Field(default_factory=list, alias="discounts")
    taxes: List[ProductTaxResponse] = Field(default_factory=list, alias="taxes")
    # backend-computed totals — never set by FE
    base_amount: Optional[float] = Field(None, alias="baseAmount")
    sale_price: Optional[float] = Field(None, alias="salePrice")

    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    data: List[ProductResponse]
    pagination: PaginationResponse
