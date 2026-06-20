"""Discount calculation service — sequential cascade per Hacienda Nota 20.

`DiscountCalculator.calculate(net_price, discounts)` applies each discount to
the *remaining* balance, never to the original (so 10% then 5% on 1000 yields
1000 -> 900 -> 855, not 850). Royalty/bonus discounts (codes 01/03) set the
`royalty_bonus_present` flag the tax calculator reads to route IVA into
`ImpuestoAsumidoEmisorFabrica`. Code 02 (royalty/bonus with VAT to customer)
sets `customer_pays_tax_on_original_base` — the IVA stays on the customer's
tab but is computed on the pre-discount base.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List

from app.dtos.common.calculation_results import DiscountLineRow, LineDiscountResult
from app.dtos.requests.product_request_dto import ProductDiscountDTO
from app.enums.hacienda_codes import FACTORY_ASSUMED_DISCOUNT_NATURES, DiscountType

ZERO = Decimal("0")
HUNDRED = Decimal("100")


class DiscountValidationError(ValueError):
    """Domain-level validation error with a stable machine code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _d(value, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class DiscountCalculator:
    """Per-line discount cascade."""

    def calculate(
        self, net_price: Decimal, discounts: List[ProductDiscountDTO]
    ) -> LineDiscountResult:
        """Apply discounts to `net_price` in cascade order; return aggregates.

        Raises:
            DiscountValidationError: when a discount of type 99 omits
                `reason` (Hacienda requires a free-form reason there).
        """
        remaining = _d(net_price)
        rows: List[DiscountLineRow] = []
        total = ZERO
        reasons: List[str] = []

        for d in discounts:
            self._validate(d)
            if d.is_amount:
                amount = _d(d.amount)
            else:
                pct = _d(d.percentage)
                amount = remaining * pct / HUNDRED
            reason = (d.reason or "").strip()
            rows.append(
                DiscountLineRow(
                    discount_type_id=d.discount_type_id,
                    amount=amount,
                    percentage=_d(d.percentage) if d.percentage is not None else None,
                    reason=reason or None,
                )
            )
            total += amount
            remaining -= amount
            if reason:
                reasons.append(reason)

        royalty_bonus_present = any(
            d.discount_type_id in FACTORY_ASSUMED_DISCOUNT_NATURES for d in discounts
        )
        customer_pays_tax_on_original_base = any(
            d.discount_type_id == DiscountType.ROYALTY_BONUS_VAT_CUSTOMER.value
            for d in discounts
        )

        return LineDiscountResult(
            subtotal_after_discount=remaining,
            total_discount_amount=total,
            per_discount=rows,
            royalty_bonus_present=royalty_bonus_present,
            customer_pays_tax_on_original_base=customer_pays_tax_on_original_base,
            discounted_reasons=reasons,
        )

    def _validate(self, d: ProductDiscountDTO) -> None:
        if d.discount_type_id == DiscountType.OTHER.value:
            reason = (d.reason or "").strip()
            if not reason:
                raise DiscountValidationError(
                    "REASON_REQUIRED",
                    "Discount type 99 (Otros) requires a non-empty reason.",
                )
