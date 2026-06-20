"""Pydantic result models for the tax/discount/line calculation engine.

Decimal everywhere — these values flow straight into Hacienda XML where the
spec is Decimal(18,5). No float intermediates; no `dict[str, Any]`.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaxLineRow(BaseModel):
    """One row of `LineTaxResult.per_tax` — the computed amount for a single tax."""

    model_config = ConfigDict(populate_by_name=True)

    tax_type_id: str = Field(...)
    amount: Decimal = Field(...)
    base_amount: Decimal = Field(...)
    # Computed amount counted toward `factory_assumed_tax` (vs the buyer-paid net).
    factory_assumed_amount: Decimal = Field(default=Decimal("0"))


class DiscountLineRow(BaseModel):
    """One row of `LineDiscountResult.per_discount` — the cascade-computed amount."""

    model_config = ConfigDict(populate_by_name=True)

    discount_type_id: str = Field(...)
    amount: Decimal = Field(...)
    percentage: Optional[Decimal] = Field(None)
    reason: Optional[str] = Field(None)


class LineTaxResult(BaseModel):
    """End-of-step tax aggregate for one product line."""

    model_config = ConfigDict(populate_by_name=True)

    iva_tax_total: Decimal = Field(default=Decimal("0"))
    other_tax_total: Decimal = Field(default=Decimal("0"))
    factory_assumed_tax: Decimal = Field(default=Decimal("0"))
    net_tax: Decimal = Field(default=Decimal("0"))
    base_amount: Decimal = Field(default=Decimal("0"))
    per_tax: List[TaxLineRow] = Field(default_factory=list)


class LineDiscountResult(BaseModel):
    """End-of-step discount aggregate for one product line."""

    model_config = ConfigDict(populate_by_name=True)

    subtotal_after_discount: Decimal = Field(...)
    total_discount_amount: Decimal = Field(default=Decimal("0"))
    per_discount: List[DiscountLineRow] = Field(default_factory=list)
    # Hacienda Nota 20: codes 01 (royalty) / 03 (bonus) reroute the IVA into
    # `ImpuestoAsumidoEmisorFabrica`. The discount calc decides this; the tax
    # calc only consumes the boolean.
    royalty_bonus_present: bool = Field(default=False)
    # Hacienda Nota 20: code 02 (Regalía / bonificación, IVA al cliente) keeps
    # the IVA on the customer but computes it on the pre-discount base, NOT on
    # the eroded subtotal. Distinct from `royalty_bonus_present` because the
    # tax still hits `net_tax` (the customer pays) instead of
    # `factory_assumed_tax` (the issuer absorbs).
    customer_pays_tax_on_original_base: bool = Field(default=False)
    # Free-form reasons (one per discount), preserved for auditing / XML
    # serializers; not consumed by the tax math.
    discounted_reasons: List[str] = Field(default_factory=list)


class LineAmountsResult(BaseModel):
    """Combined per-line result: discounts + taxes + final sale price."""

    model_config = ConfigDict(populate_by_name=True)

    total_amount: Decimal = Field(...)
    subtotal: Decimal = Field(...)
    sale_price: Decimal = Field(...)
    discount: LineDiscountResult
    tax: LineTaxResult
