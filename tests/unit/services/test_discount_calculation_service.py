"""Unit tests for `DiscountCalculator`.

Cover the sequential cascade, royalty/bonus flag wiring, the
`customer_pays_tax_on_original_base` flag for code 02, and the
reason-required validation on type 99.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.dtos.requests.product_request_dto import ProductDiscountDTO
from app.enums.hacienda_codes import DiscountType
from app.services.discount_calculation_service import (
    DiscountCalculator,
    DiscountValidationError,
)

D = Decimal


def _disc(
    *,
    type_id: DiscountType,
    percentage: Decimal | None = None,
    amount: Decimal | None = None,
    reason: str | None = None,
) -> ProductDiscountDTO:
    return ProductDiscountDTO(
        discount_type_id=type_id.value,
        percentage=float(percentage) if percentage is not None else None,
        amount=float(amount) if amount is not None else None,
        is_amount=amount is not None,
        reason=reason,
    )


class TestDiscountCalculator:
    def setup_method(self) -> None:
        self.calc = DiscountCalculator()

    def test_cascade_10_then_5_then_5_on_1000(self) -> None:
        # 1000 -> 900 (10%) -> 855 (5%) -> 812.25 (5%).
        discounts = [
            _disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, percentage=D("10")),
            _disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, percentage=D("5")),
            _disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, percentage=D("5")),
        ]
        result = self.calc.calculate(D("1000"), discounts)
        assert result.per_discount[0].amount == D("100")
        assert result.per_discount[1].amount == D("45")
        assert result.per_discount[2].amount == D("42.75")
        assert result.subtotal_after_discount == D("812.25")
        assert result.total_discount_amount == D("187.75")

    def test_amount_discount_used_as_is(self) -> None:
        discounts = [
            _disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, amount=D("123.45"))
        ]
        result = self.calc.calculate(D("1000"), discounts)
        assert result.per_discount[0].amount == D("123.45")
        assert result.subtotal_after_discount == D("876.55")

    def test_royalty_bonus_flag_set_when_01_or_03_present(self) -> None:
        for code in (DiscountType.ROYALTY, DiscountType.BONUS):
            result = self.calc.calculate(
                D("1000"), [_disc(type_id=code, percentage=D("10"))]
            )
            assert result.royalty_bonus_present is True
            # Code 01/03 alone does NOT set the code-02 flag.
            assert result.customer_pays_tax_on_original_base is False

    def test_royalty_bonus_flag_off_when_only_02_present(self) -> None:
        result = self.calc.calculate(
            D("1000"),
            [_disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, percentage=D("10"))],
        )
        assert result.royalty_bonus_present is False

    def test_customer_pays_tax_on_original_base_flag_set_for_02(self) -> None:
        result = self.calc.calculate(
            D("1000"),
            [_disc(type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER, percentage=D("10"))],
        )
        assert result.customer_pays_tax_on_original_base is True

    def test_customer_pays_tax_flag_off_when_no_02_present(self) -> None:
        for code in (DiscountType.ROYALTY, DiscountType.BONUS):
            result = self.calc.calculate(
                D("1000"), [_disc(type_id=code, percentage=D("10"))]
            )
            assert result.customer_pays_tax_on_original_base is False

    def test_reason_required_for_99(self) -> None:
        # Pydantic-level validator already raises a ValueError on the DTO build,
        # so we exercise the calc by constructing the DTO with a non-empty
        # reason, then blanking it out before passing to the calc.
        bad = _disc(type_id=DiscountType.OTHER, percentage=D("10"), reason="dummy")
        bad.reason = ""  # bypass DTO validator to test calc-level guard
        with pytest.raises(DiscountValidationError) as ei:
            self.calc.calculate(D("1000"), [bad])
        assert ei.value.code == "REASON_REQUIRED"

    def test_reason_accepted_for_99(self) -> None:
        result = self.calc.calculate(
            D("1000"),
            [
                _disc(
                    type_id=DiscountType.OTHER,
                    percentage=D("10"),
                    reason="end-of-season",
                )
            ],
        )
        assert result.per_discount[0].amount == D("100")
        assert result.discounted_reasons == ["end-of-season"]

    def test_empty_discount_list_returns_full_subtotal(self) -> None:
        result = self.calc.calculate(D("500"), [])
        assert result.subtotal_after_discount == D("500")
        assert result.total_discount_amount == D("0")
        assert result.royalty_bonus_present is False
        assert result.customer_pays_tax_on_original_base is False
