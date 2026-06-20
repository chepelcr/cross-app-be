"""Line-level orchestrator — applies discounts, then taxes, then aggregates.

Replaces the old `app/utils/product_calculations.py` god-function. Pure Decimal
math on top of the two single-responsibility services (discount + tax).
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.common.calculation_results import LineAmountsResult
from app.dtos.requests.product_request_dto import ProductDiscountDTO, ProductTaxDTO
from app.services.discount_calculation_service import DiscountCalculator
from app.services.tax_calculation_service import TaxCalculator

ZERO = Decimal("0")
ONE = Decimal("1")


def _d(value, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class LineInput(BaseModel):
    """Subset of a product/line DTO the calc needs.

    Decoupled from `Product` and `ProductRequestDTO` on purpose so the
    orchestrator stays testable without a DB or HTTP layer.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    price: Decimal
    quantity: Decimal = Field(default=ONE)
    is_packaged: bool = Field(default=False)
    detail_quantity: Decimal = Field(default=ONE)
    discounts: List[ProductDiscountDTO] = Field(default_factory=list)
    taxes: List[ProductTaxDTO] = Field(default_factory=list)
    manual_base_amount: Optional[Decimal] = Field(default=None)
    # Pre-discount line subtotal (`unit_price × detail_quantity` for line
    # carts; `price × quantity` for packaged-product previews). Hacienda Nota
    # 20 requires this as the IVA base when royalty/bonus codes 01/03 OR code
    # 02 (VAT-to-customer) are present. When None, the orchestrator derives it
    # from the same numbers used to compute `total_amount`.
    monto_total_original: Optional[Decimal] = Field(default=None)


class LineCalculator:
    """Drives discount → tax → aggregate in the right order."""

    def __init__(
        self,
        discount_calc: Optional[DiscountCalculator] = None,
        tax_calc: Optional[TaxCalculator] = None,
    ) -> None:
        self._discounts = discount_calc or DiscountCalculator()
        self._taxes = tax_calc or TaxCalculator()

    def compute(
        self,
        line: LineInput,
        cabys_code: Optional[str] = None,
    ) -> LineAmountsResult:
        price = _d(line.price)
        quantity = _d(line.quantity) if line.is_packaged else ONE
        total_amount = price * quantity

        # `monto_total_original` defaults to `total_amount` when the caller
        # doesn't pass it explicitly; both represent the pre-discount line
        # subtotal (Hacienda `MontoTotal`).
        monto_total_original = (
            _d(line.monto_total_original)
            if line.monto_total_original is not None
            else total_amount
        )

        discount_result = self._discounts.calculate(total_amount, line.discounts)
        subtotal = discount_result.subtotal_after_discount

        tax_result = self._taxes.compute_line_taxes(
            taxes=line.taxes,
            subtotal=subtotal,
            detail_quantity=_d(line.detail_quantity) or ONE,
            cabys_code=cabys_code,
            royalty_bonus_present=discount_result.royalty_bonus_present,
            customer_pays_tax_on_original_base=(
                discount_result.customer_pays_tax_on_original_base
            ),
            monto_total_original=monto_total_original,
            ivace_base_override=_d(line.manual_base_amount)
            if line.manual_base_amount is not None
            else None,
        )

        # The buyer-paid total only includes net (factory-assumed is owed
        # upstream by the factory, not by the customer).
        sale_price = subtotal + tax_result.net_tax

        return LineAmountsResult(
            total_amount=total_amount,
            subtotal=subtotal,
            sale_price=sale_price,
            discount=discount_result,
            tax=tax_result,
        )
