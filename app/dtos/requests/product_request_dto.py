from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.files import ImageDTO


# ---------------------------------------------------------------------------
# Fiscal / Hacienda e-invoicing nested DTOs (input only — no computed fields)
# ---------------------------------------------------------------------------

class TaxRateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="id")
    percentage: float = Field(..., alias="percentage")


class TaxFactorDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="id")
    factor: float = Field(..., alias="factor")


class TaxAmountDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="id")
    amount: float = Field(..., alias="amount")


class TaxSpecialFieldsDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    quantity: Optional[float] = Field(None, alias="quantity")
    percentage: Optional[float] = Field(None, alias="percentage")
    proportion: Optional[float] = Field(None, alias="proportion")
    volume_consumption: Optional[float] = Field(None, alias="volumeConsumption")
    tax_amount: Optional[TaxAmountDTO] = Field(None, alias="taxAmount")


class ProductCodeDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code_type_id: str = Field(..., alias="codeTypeId")
    number: str = Field(..., alias="number")
    description: Optional[str] = Field(None, alias="description")


class ProductDiscountDTO(BaseModel):
    """Discount input — no 'amount' field; discount amounts are backend-calculated."""

    model_config = ConfigDict(populate_by_name=True)

    discount_type_id: str = Field(..., alias="discountTypeId")
    percentage: Optional[float] = Field(None, alias="percentage")
    reason: Optional[str] = Field(None, alias="reason")
    is_amount: Optional[bool] = Field(None, alias="isAmount")


class ProductTaxDTO(BaseModel):
    """Tax input — no 'amount' field; tax amounts are backend-calculated."""

    model_config = ConfigDict(populate_by_name=True)

    tax_type_id: str = Field(..., alias="taxTypeId")
    tax_rate: Optional[TaxRateDTO] = Field(None, alias="taxRate")
    tax_factor: Optional[TaxFactorDTO] = Field(None, alias="taxFactor")
    other_tax_type: Optional[str] = Field(None, alias="otherTaxType")
    special_fields: Optional[TaxSpecialFieldsDTO] = Field(None, alias="specialFields")
    is_amount: Optional[bool] = Field(None, alias="isAmount")


class CabysInputDTO(BaseModel):
    """Frontend sends full CABYS record so the backend can upsert the catalog."""

    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="code")
    name: str = Field(..., alias="name")
    type: int = Field(..., alias="type")


# ---------------------------------------------------------------------------
# Main request DTO
# ---------------------------------------------------------------------------

class ProductRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # Basic product fields
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    units_per_box: Optional[int] = Field(None, alias="unitsPerBox")
    price: Optional[int] = Field(None, alias="price")
    category_id: Optional[str] = Field(None, alias="categoryId")
    image: Optional[ImageDTO] = Field(None, alias="image")

    # Fiscal / Hacienda e-invoicing fields
    cabys: Optional[CabysInputDTO] = Field(None, alias="cabys")
    unit_id: Optional[int] = Field(None, alias="unitId")
    commercial_unit_measure: Optional[str] = Field(None, alias="commercialUnitMeasure")
    is_packaged: Optional[bool] = Field(None, alias="isPackaged")
    quantity: Optional[float] = Field(None, alias="quantity")
    unit_price: Optional[float] = Field(None, alias="unitPrice")
    customs_part: Optional[str] = Field(None, alias="customsPart")
    codes: Optional[List[ProductCodeDTO]] = Field(None, alias="codes")
    discounts: Optional[List[ProductDiscountDTO]] = Field(None, alias="discounts")
    taxes: Optional[List[ProductTaxDTO]] = Field(None, alias="taxes")
    # Manual override for IVACE-07 only; not required in other scenarios
    base_amount: Optional[float] = Field(None, alias="baseAmount")
    # salePrice is NEVER a request field — always computed by the backend
