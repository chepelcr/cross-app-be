from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.dtos.files import ImageDTO
from app.enums.hacienda_codes import (
    DiscountType,
    IvaCollectedFactory,
    TaxRateCode,
    TaxType,
)
from app.enums.product_type import ProductType


# ---------------------------------------------------------------------------
# Fiscal / Hacienda e-invoicing nested DTOs (input only — no computed fields)
# ---------------------------------------------------------------------------

class TaxRateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None)
    percentage: float = Field(...)
    # Hacienda Nota 8.1 rate code (01–11). Optional on input because legacy
    # payloads predate the catalog; new payloads should send it.
    code: Optional[str] = Field(None)

    @field_validator("code")
    @classmethod
    def _validate_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {m.value for m in TaxRateCode}
        if value not in allowed:
            raise ValueError(
                f"tax_rate.code {value!r} is not a valid Hacienda Nota 8.1 code."
            )
        return value


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


class ProductDiscountDTO(BaseModel):
    """Discount input. `amount` is None on inbound requests — the BE calc sets
    it before persistence so the JSONB row carries the computed value.

    `reason` is the single canonical free-form descriptor:
    - codes 01 / 02 / 03 (Royalty / Royalty-bonus-VAT-to-customer / Bonus):
      the FE auto-fills it from the discount-type label.
    - code 99 (Otros): the user enters the Nota-20 nature text — required.
    """

    model_config = ConfigDict(populate_by_name=True)

    discount_type_id: str = Field(...)
    percentage: Optional[float] = Field(None)
    reason: Optional[str] = Field(None)
    is_amount: Optional[bool] = Field(None)
    amount: Optional[float] = Field(None)

    @model_validator(mode="after")
    def _validate_reason(self) -> "ProductDiscountDTO":
        if self.discount_type_id == DiscountType.OTHER.value:
            reason = (self.reason or "").strip()
            if not reason:
                raise ValueError(
                    "Discount type 99 (Otros) requires a non-empty reason."
                )
        return self


class ProductTaxDTO(BaseModel):
    """Tax input. `amount` is None on inbound requests — the BE calc sets it
    before persistence so the JSONB row carries the computed value.

    `special_fields` is validated per Hacienda Nota 7 for the codes that
    consume per-unit/per-volume parameters:
    - IUC (03), IPT (06), ISEC (12): `quantity` + `tax_amount.id` required.
    - ISEBA (04): `quantity` + `percentage` + `tax_amount.id` required.
    - ISEBEC (05): `quantity` + `volume_consumption` + `tax_amount.id`
      required. The alcoholic-CABYS `percentage` requirement is enforced in
      the service layer where the CABYS row is available.
    """

    model_config = ConfigDict(populate_by_name=True)

    tax_type_id: str = Field(...)
    tax_rate: Optional[TaxRateDTO] = Field(None)
    tax_factor: Optional[TaxFactorDTO] = Field(None)
    other_tax_type: Optional[str] = Field(None)
    special_fields: Optional[TaxSpecialFieldsDTO] = Field(None)
    is_amount: Optional[bool] = Field(None)
    amount: Optional[float] = Field(None)

    @model_validator(mode="after")
    def _validate_special_fields(self) -> "ProductTaxDTO":
        code = self.tax_type_id
        # Per-Hacienda-code required-key map for special_fields.
        required_keys_by_code: dict[str, tuple[str, ...]] = {
            TaxType.IUC.value: ("quantity", "tax_amount_id"),
            TaxType.IPT.value: ("quantity", "tax_amount_id"),
            TaxType.ISEC.value: ("quantity", "tax_amount_id"),
            TaxType.ISEBA.value: ("quantity", "percentage", "tax_amount_id"),
            TaxType.ISEBEC.value: (
                "quantity",
                "volume_consumption",
                "tax_amount_id",
            ),
        }
        required = required_keys_by_code.get(code)
        if not required:
            return self
        sf = self.special_fields
        if sf is None:
            raise ValueError(
                f"Tax code {code} requires special_fields with "
                f"keys {required}."
            )
        missing: list[str] = []
        for key in required:
            if key == "tax_amount_id":
                if sf.tax_amount is None or not sf.tax_amount.id:
                    missing.append("tax_amount.id")
            else:
                value = getattr(sf, key, None)
                if value is None:
                    missing.append(key)
        if missing:
            raise ValueError(
                f"Tax code {code} is missing required special_fields: "
                f"{missing}."
            )
        return self


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
    # Preferred path: an already-uploaded asset URL (org media library / S3).
    # Stored directly when provided; empty string clears it.
    image_url: Optional[str] = Field(None)

    # Inventory / catalogue fields
    stock_quantity: Optional[int] = Field(None)
    low_stock_threshold: Optional[int] = Field(None)
    track_inventory: Optional[bool] = Field(None)
    is_service: Optional[bool] = Field(None)
    # First-class product kind: product | service | program.
    type: Optional[str] = Field(None)
    on_sale: Optional[bool] = Field(None)
    # Storefront "Oferta" flag (independent of the on_sale discount mechanic).
    is_offer: Optional[bool] = Field(None)
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

    # ---- Exemption block (Hacienda v4.4 Exoneracion) -----------------------
    # `Exoneracion.TipoDocumento` 01–11 (Nota 10.1). Optional everywhere.
    exemption_authorization_code: Optional[str] = Field(None)
    # `Exoneracion.TarifaExonerada` Decimal(4,2)
    exempted_rate: Optional[float] = Field(None)
    # `Exoneracion.MontoExoneracion` Decimal(18,5)
    exemption_amount: Optional[float] = Field(None)
    # `IVACobradoFabrica` (01 / 02). Validated against the enum.
    iva_collected_factory: Optional[str] = Field(None)
    # data-services FK for the factory-tax-charge row. Round-tripped from the
    # FE so the canonical id-on-product survives a save/edit cycle. Distinct
    # from the line-level `factory_tax` code derived at cart-add time.
    factory_tax_charge_id: Optional[int] = Field(None)

    @field_validator("type")
    @classmethod
    def _validate_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not ProductType.is_valid(value):
            raise ValueError(
                f"type {value!r} is not a valid product type "
                f"(allowed: {ProductType.values()})."
            )
        return value

    @field_validator("iva_collected_factory")
    @classmethod
    def _validate_iva_collected_factory(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {m.value for m in IvaCollectedFactory}
        if value not in allowed:
            raise ValueError(
                f"iva_collected_factory {value!r} not in IvaCollectedFactory enum."
            )
        return value
