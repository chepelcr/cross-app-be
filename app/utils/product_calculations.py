"""Pure Python tax and discount calculation engine for Costa Rica Hacienda e-invoicing.

No SQLAlchemy dependencies — independently testable.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.enums.hacienda_codes import DiscountType, TaxType


def validate_discounts(discounts: list[dict]) -> None:
    """Validate discount list according to Hacienda rules.

    Raises:
        ValueError: if any validation rule is violated.
    """
    if len(discounts) > 5:
        raise ValueError("A product may have at most 5 discounts.")

    total_pct = Decimal("0")
    for d in discounts:
        pct = d.get("percentage")
        if pct is not None:
            total_pct += Decimal(str(pct))
        type_id = d.get("discountTypeId")
        if type_id == DiscountType.OTHER:
            reason = d.get("reason") or ""
            if len(reason.strip()) < 5:
                raise ValueError(
                    "Discounts of type '99' (Otros) require a reason of at least 5 characters."
                )

    if total_pct > Decimal("100"):
        raise ValueError(
            f"Total discount percentage ({total_pct}%) cannot exceed 100%."
        )


def validate_taxes(taxes: list[dict]) -> None:
    """Validate tax list according to Hacienda rules.

    Raises:
        ValueError: if any validation rule is violated.
    """
    for t in taxes:
        tax_type = t.get("taxTypeId")

        if tax_type in (TaxType.IVA, TaxType.IVACE):
            if t.get("taxRate") is None:
                raise ValueError(
                    f"Tax type '{tax_type}' (IVA/IVACE) requires taxRate."
                )

        if tax_type == TaxType.IVARBU:
            if t.get("taxFactor") is None:
                raise ValueError(
                    "Tax type '08' (IVARBU) requires taxFactor."
                )

        if tax_type in (TaxType.IUC, TaxType.ISEBA, TaxType.ISEBEC, TaxType.IPT):
            sf = t.get("specialFields")
            if not sf or sf.get("taxAmount") is None:
                raise ValueError(
                    f"Tax type '{tax_type}' requires specialFields.taxAmount."
                )

        if tax_type == TaxType.OTHERS:
            if not t.get("otherTaxType"):
                raise ValueError(
                    "Tax type '99' (Otros) requires otherTaxType."
                )


def calculate_product_totals(
    price: Decimal,
    quantity: Decimal,
    is_packaged: bool,
    discounts: list[dict],
    taxes: list[dict],
    cabys_code: Optional[str] = None,
    manual_base_amount: Optional[Decimal] = None,
    detail_quantity: Decimal = Decimal("1"),
) -> tuple[Decimal, Decimal]:
    """Calculate base_amount and sale_price, mutating discount/tax dicts with computed amounts.

    Args:
        price: Unit price of the product.
        quantity: Quantity (used when is_packaged is True).
        is_packaged: If True, totalAmount = price * quantity; else totalAmount = price.
        discounts: List of discount dicts (mutated in-place with computed 'amount').
        taxes: List of tax dicts (mutated in-place with computed 'amount').
        cabys_code: CABYS code string (used for ISEBEC logic).
        manual_base_amount: Override for IVACE-07 special base amount.
        detail_quantity: Order line quantity (used in some special tax formulas).

    Returns:
        Tuple of (base_amount, sale_price) as Decimal values.
    """
    price = Decimal(str(price))
    quantity = Decimal(str(quantity))

    # Step 1: Total amount
    if is_packaged:
        total_amount = price * quantity
    else:
        total_amount = price

    # Step 2: Discount amount
    discount_amount = Decimal("0")
    for d in discounts:
        if d.get("isAmount"):
            amt = Decimal(str(d.get("amount", 0) or 0))
        else:
            pct = Decimal(str(d.get("percentage", 0) or 0))
            amt = price * pct / Decimal("100")
        d["amount"] = float(amt)
        discount_amount += amt

    # Step 3: Subtotal
    subtotal = total_amount - discount_amount

    # Step 4: Base amount (may be overridden for IVACE)
    if manual_base_amount is not None:
        base_amount = Decimal(str(manual_base_amount))
    else:
        base_amount = subtotal

    # Step A: Special taxes (02, 03, 04, 05, 06, 12) — mutate t["amount"], may adjust base_amount
    for t in taxes:
        tax_type = t.get("taxTypeId")

        if tax_type == TaxType.ISC:
            rate = Decimal(str((t.get("taxRate") or {}).get("percentage", 0) or 0))
            amount = subtotal * rate / Decimal("100")
            t["amount"] = float(amount)
            base_amount += amount

        elif tax_type == TaxType.IUC:
            sf = t.get("specialFields") or {}
            tax_amt = sf.get("taxAmount") or {}
            unit_amount = Decimal(str(tax_amt.get("amount", 0) or 0))
            sf_qty = Decimal(str(sf.get("quantity", 1) or 1))
            amount = sf_qty * unit_amount
            t["amount"] = float(amount)
            # IUC does not adjust base_amount per spec

        elif tax_type == TaxType.ISEBA:
            sf = t.get("specialFields") or {}
            tax_amt = sf.get("taxAmount") or {}
            sf_qty = Decimal(str(sf.get("quantity", 1) or 1))
            sf_pct = Decimal(str(sf.get("percentage", 0) or 0))
            unit_amount = Decimal(str(tax_amt.get("amount", 0) or 0))
            amount = detail_quantity * (sf_qty * sf_pct / Decimal("100")) * unit_amount
            t["amount"] = float(amount)
            base_amount += amount

        elif tax_type == TaxType.ISEBEC:
            sf = t.get("specialFields") or {}
            tax_amt = sf.get("taxAmount") or {}
            sf_qty = Decimal(str(sf.get("quantity", 1) or 1))
            vol = Decimal(str(sf.get("volumeConsumption", 1) or 1))
            tax_unit = Decimal(str(tax_amt.get("amount", 0) or 0))
            if cabys_code and cabys_code.startswith("2202"):
                amount = detail_quantity * sf_qty * (tax_unit / vol)
            else:
                amount = sf_qty * vol * tax_unit
            t["amount"] = float(amount)
            base_amount += amount

        elif tax_type == TaxType.IPT:
            sf = t.get("specialFields") or {}
            tax_amt = sf.get("taxAmount") or {}
            sf_qty = Decimal(str(sf.get("quantity", 1) or 1))
            unit_amount = Decimal(str(tax_amt.get("amount", 0) or 0))
            amount = detail_quantity * sf_qty * unit_amount
            t["amount"] = float(amount)
            # IPT does not adjust base_amount per spec

        elif tax_type == TaxType.ISEC:
            rate = Decimal(str((t.get("taxRate") or {}).get("percentage", 0) or 0))
            amount = subtotal * rate / Decimal("100")
            t["amount"] = float(amount)
            base_amount += amount

    # Step B: Others (99)
    for t in taxes:
        if t.get("taxTypeId") == TaxType.OTHERS:
            rate = Decimal(str((t.get("taxRate") or {}).get("percentage", 0) or 0))
            amount = base_amount * rate / Decimal("100")
            t["amount"] = float(amount)

    # Step C: IVA / IVACE / IVARBU
    for t in taxes:
        tax_type = t.get("taxTypeId")

        if tax_type in (TaxType.IVA, TaxType.IVACE):
            rate = Decimal(str((t.get("taxRate") or {}).get("percentage", 0) or 0))
            amount = base_amount * rate / Decimal("100")
            t["amount"] = float(amount)

        elif tax_type == TaxType.IVARBU:
            tf = t.get("taxFactor") or {}
            factor = Decimal(str(tf.get("factor", 0) or 0))
            amount = factor * subtotal
            t["amount"] = float(amount)

    # Step 8: Sale price = subtotal + sum of all tax amounts
    total_taxes = sum(Decimal(str(t.get("amount", 0) or 0)) for t in taxes)
    sale_price = subtotal + total_taxes

    return base_amount, sale_price
