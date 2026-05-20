"""Pure-Python tax/discount engine for Costa Rica Hacienda e-invoicing.

Operates on the request DTOs (ProductDiscountDTO / ProductTaxDTO) directly —
no `dict.get(...)` indirection, no key-format mismatches. Pydantic models are
mutable by default, so the calc populates each entry's `.amount` field in
place; the service layer then dumps to JSONB for storage.

No SQLAlchemy or DB dependencies — independently testable.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.dtos.requests.product_request_dto import (
    ProductDiscountDTO,
    ProductTaxDTO,
)
from app.enums.hacienda_codes import DiscountType, TaxType


def validate_discounts(discounts: list[ProductDiscountDTO]) -> None:
    """Validate discount list according to Hacienda rules.

    Raises:
        ValueError: if any validation rule is violated.
    """
    if len(discounts) > 5:
        raise ValueError("A product may have at most 5 discounts.")

    total_pct = Decimal("0")
    for d in discounts:
        if d.percentage is not None:
            total_pct += Decimal(str(d.percentage))
        if d.discount_type_id == DiscountType.OTHER:
            reason = (d.reason or "").strip()
            if len(reason) < 5:
                raise ValueError(
                    "Discounts of type '99' (Otros) require a reason of at least 5 characters."
                )

    if total_pct > Decimal("100"):
        raise ValueError(
            f"Total discount percentage ({total_pct}%) cannot exceed 100%."
        )


def validate_taxes(taxes: list[ProductTaxDTO]) -> None:
    """Validate tax list according to Hacienda rules.

    Raises:
        ValueError: if any validation rule is violated.
    """
    for t in taxes:
        tax_type = t.tax_type_id

        if tax_type in (TaxType.IVA, TaxType.IVACE):
            if t.tax_rate is None:
                raise ValueError(
                    f"Tax type '{tax_type}' (IVA/IVACE) requires tax_rate."
                )

        if tax_type == TaxType.IVARBU:
            if t.tax_factor is None:
                raise ValueError(
                    "Tax type '08' (IVARBU) requires tax_factor."
                )

        if tax_type in (TaxType.IUC, TaxType.ISEBA, TaxType.ISEBEC, TaxType.IPT):
            if t.special_fields is None or t.special_fields.tax_amount is None:
                raise ValueError(
                    f"Tax type '{tax_type}' requires special_fields.tax_amount."
                )

        if tax_type == TaxType.OTHERS:
            if not t.other_tax_type:
                raise ValueError(
                    "Tax type '99' (Otros) requires other_tax_type."
                )


def _to_decimal(value, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


def calculate_product_totals(
    price: Decimal,
    quantity: Decimal,
    is_packaged: bool,
    discounts: list[ProductDiscountDTO],
    taxes: list[ProductTaxDTO],
    cabys_code: Optional[str] = None,
    manual_base_amount: Optional[Decimal] = None,
    detail_quantity: Decimal = Decimal("1"),
) -> tuple[Decimal, Decimal]:
    """Compute base_amount and sale_price, populating each DTO's `.amount`.

    Mutates the DTOs in place — every discount and tax entry receives a
    computed `.amount` reflecting the Hacienda formula for its type. The
    service layer dumps to JSONB after this returns so the stored row
    carries those values.

    Returns:
        (base_amount, sale_price) as Decimal.
    """
    price = Decimal(str(price))
    quantity = Decimal(str(quantity))

    # Step 1: Total amount (line gross, before any line-level discount)
    total_amount = price * quantity if is_packaged else price

    # Step 2: Discount amounts (mutate each discount.amount)
    discount_amount = Decimal("0")
    for d in discounts:
        if d.is_amount:
            amt = _to_decimal(d.amount)
        else:
            pct = _to_decimal(d.percentage)
            amt = price * pct / Decimal("100")
        d.amount = float(amt)
        discount_amount += amt

    # Step 3: Subtotal
    subtotal = total_amount - discount_amount

    # Step 4: Base amount (may be overridden for IVACE-07)
    base_amount: Decimal = (
        Decimal(str(manual_base_amount)) if manual_base_amount is not None else subtotal
    )

    # Step A — Special / per-unit taxes (ISC, IUC, ISEBA, ISEBEC, IPT, ISEC).
    # Each tax populates its `.amount`; some adjust base_amount.
    for t in taxes:
        tax_type = t.tax_type_id

        if tax_type == TaxType.ISC:
            rate = _to_decimal(t.tax_rate.percentage if t.tax_rate else None)
            amount = subtotal * rate / Decimal("100")
            t.amount = float(amount)
            base_amount += amount

        elif tax_type == TaxType.IUC:
            sf = t.special_fields
            unit_amount = _to_decimal(sf.tax_amount.amount if sf and sf.tax_amount else None)
            sf_qty = _to_decimal(sf.quantity if sf else None, default="1") or Decimal("1")
            amount = sf_qty * unit_amount
            t.amount = float(amount)
            # IUC does not adjust base_amount.

        elif tax_type == TaxType.ISEBA:
            sf = t.special_fields
            unit_amount = _to_decimal(sf.tax_amount.amount if sf and sf.tax_amount else None)
            sf_qty = _to_decimal(sf.quantity if sf else None, default="1") or Decimal("1")
            sf_pct = _to_decimal(sf.percentage if sf else None)
            amount = detail_quantity * (sf_qty * sf_pct / Decimal("100")) * unit_amount
            t.amount = float(amount)
            base_amount += amount

        elif tax_type == TaxType.ISEBEC:
            sf = t.special_fields
            tax_unit = _to_decimal(sf.tax_amount.amount if sf and sf.tax_amount else None)
            sf_qty = _to_decimal(sf.quantity if sf else None, default="1") or Decimal("1")
            vol = _to_decimal(sf.volume_consumption if sf else None, default="1") or Decimal("1")
            if cabys_code and cabys_code.startswith("2202"):
                amount = detail_quantity * sf_qty * (tax_unit / vol)
            else:
                amount = sf_qty * vol * tax_unit
            t.amount = float(amount)
            base_amount += amount

        elif tax_type == TaxType.IPT:
            sf = t.special_fields
            unit_amount = _to_decimal(sf.tax_amount.amount if sf and sf.tax_amount else None)
            sf_qty = _to_decimal(sf.quantity if sf else None, default="1") or Decimal("1")
            amount = detail_quantity * sf_qty * unit_amount
            t.amount = float(amount)
            # IPT does not adjust base_amount.

        elif tax_type == TaxType.ISEC:
            rate = _to_decimal(t.tax_rate.percentage if t.tax_rate else None)
            amount = subtotal * rate / Decimal("100")
            t.amount = float(amount)
            base_amount += amount

    # Step B — Others (99), applied to the now-updated base_amount.
    for t in taxes:
        if t.tax_type_id == TaxType.OTHERS:
            rate = _to_decimal(t.tax_rate.percentage if t.tax_rate else None)
            t.amount = float(base_amount * rate / Decimal("100"))

    # Step C — IVA family (01, 07, 08).
    for t in taxes:
        tax_type = t.tax_type_id

        if tax_type in (TaxType.IVA, TaxType.IVACE):
            rate = _to_decimal(t.tax_rate.percentage if t.tax_rate else None)
            t.amount = float(base_amount * rate / Decimal("100"))

        elif tax_type == TaxType.IVARBU:
            factor = _to_decimal(t.tax_factor.factor if t.tax_factor else None)
            t.amount = float(factor * subtotal)

    # Step 8: Sale price = subtotal + sum of all computed tax amounts
    total_taxes = sum((_to_decimal(t.amount) for t in taxes), Decimal("0"))
    sale_price = subtotal + total_taxes

    return base_amount, sale_price
