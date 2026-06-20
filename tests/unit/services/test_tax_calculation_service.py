"""Per-Hacienda-code unit tests for `TaxCalculator`.

One method per code (01–08, 12, 99) + the ISEBEC non-alcoholic branch driven
by the CABYS prefix.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.dtos.requests.product_request_dto import (
    ProductTaxDTO,
    TaxAmountDTO,
    TaxFactorDTO,
    TaxRateDTO,
    TaxSpecialFieldsDTO,
)
from app.enums.hacienda_codes import CabysSpecialPrefix, TaxRateCode, TaxType
from app.services.tax_calculation_service import TaxCalculator

D = Decimal


def _make_tax(
    tax_type: TaxType,
    *,
    rate: Decimal | None = None,
    rate_code: TaxRateCode | None = None,
    factor: Decimal | None = None,
    sf_quantity: Decimal | None = None,
    sf_percentage: Decimal | None = None,
    sf_volume: Decimal | None = None,
    sf_amount: Decimal | None = None,
) -> ProductTaxDTO:
    return ProductTaxDTO(
        tax_type_id=tax_type.value,
        tax_rate=(
            TaxRateDTO(
                percentage=float(rate),
                code=rate_code.value if rate_code else None,
            )
            if rate is not None
            else None
        ),
        tax_factor=(
            TaxFactorDTO(id="factor-1", factor=float(factor)) if factor is not None else None
        ),
        special_fields=(
            TaxSpecialFieldsDTO(
                quantity=float(sf_quantity) if sf_quantity is not None else None,
                percentage=float(sf_percentage) if sf_percentage is not None else None,
                volume_consumption=float(sf_volume) if sf_volume is not None else None,
                tax_amount=(
                    TaxAmountDTO(id="ta-1", amount=float(sf_amount))
                    if sf_amount is not None
                    else None
                ),
            )
            if any(
                v is not None
                for v in (sf_quantity, sf_percentage, sf_volume, sf_amount)
            )
            else None
        ),
    )


def _run(calc, taxes, *, subtotal, cabys=None, detail_quantity=D("1")):
    return calc.compute_line_taxes(
        taxes=taxes,
        subtotal=subtotal,
        detail_quantity=detail_quantity,
        cabys_code=cabys,
        monto_total_original=subtotal,
    )


class TestTaxCalculator:
    def setup_method(self) -> None:
        self.calc = TaxCalculator()

    def test_iva_01_general_13(self) -> None:
        # 13% IVA on a 1000 subtotal = 130.
        result = _run(
            self.calc,
            [_make_tax(TaxType.IVA, rate=D("13"), rate_code=TaxRateCode.GENERAL_13)],
            subtotal=D("1000"),
        )
        assert result.iva_tax_total == D("130")
        assert result.net_tax == D("130")
        assert result.base_amount == D("1000")
        assert result.factory_assumed_tax == D("0")

    def test_isc_02_increments_base(self) -> None:
        # 10% ISC on 1000 = 100; base climbs from 1000 to 1100.
        result = _run(
            self.calc,
            [_make_tax(TaxType.ISC, rate=D("10"))],
            subtotal=D("1000"),
        )
        assert result.per_tax[0].amount == D("100")
        assert result.other_tax_total == D("100")
        assert result.base_amount == D("1100")

    def test_iuc_03_per_unit(self) -> None:
        # 5 units × 200 = 1000; IUC does not touch base.
        result = _run(
            self.calc,
            [_make_tax(TaxType.IUC, sf_quantity=D("5"), sf_amount=D("200"))],
            subtotal=D("1000"),
        )
        assert result.per_tax[0].amount == D("1000")
        assert result.base_amount == D("1000")

    def test_iseba_04_with_detail_quantity(self) -> None:
        # detail_quantity (2) × (qty 4 × pct 50% / 100) × unit 100 = 2 × 2 × 100 = 400.
        result = _run(
            self.calc,
            [
                _make_tax(
                    TaxType.ISEBA,
                    sf_quantity=D("4"),
                    sf_percentage=D("50"),
                    sf_amount=D("100"),
                )
            ],
            subtotal=D("1000"),
            detail_quantity=D("2"),
        )
        assert result.per_tax[0].amount == D("400")
        # ISEBA grows the base.
        assert result.base_amount == D("1400")

    def test_isebec_05_alcoholic_default_branch(self) -> None:
        # No CABYS prefix → alcoholic formula: qty × volume × unit = 2 × 3 × 50 = 300.
        result = _run(
            self.calc,
            [
                _make_tax(
                    TaxType.ISEBEC,
                    sf_quantity=D("2"),
                    sf_volume=D("3"),
                    sf_amount=D("50"),
                )
            ],
            subtotal=D("1000"),
        )
        assert result.per_tax[0].amount == D("300")

    def test_isebec_05_non_alcoholic_via_cabys_2202(self) -> None:
        # 2202* CABYS triggers: detail_quantity (4) × qty (2) × (unit/volume) (10/2=5) = 40.
        result = _run(
            self.calc,
            [
                _make_tax(
                    TaxType.ISEBEC,
                    sf_quantity=D("2"),
                    sf_volume=D("2"),
                    sf_amount=D("10"),
                )
            ],
            subtotal=D("1000"),
            cabys=CabysSpecialPrefix.ISEBEC_NON_ALCOHOLIC.value + "12345",
            detail_quantity=D("4"),
        )
        assert result.per_tax[0].amount == D("40")

    def test_ipt_06_per_unit_with_detail_quantity(self) -> None:
        # detail_quantity (3) × qty (4) × unit (5) = 60. IPT does not adjust base.
        result = _run(
            self.calc,
            [_make_tax(TaxType.IPT, sf_quantity=D("4"), sf_amount=D("5"))],
            subtotal=D("1000"),
            detail_quantity=D("3"),
        )
        assert result.per_tax[0].amount == D("60")
        assert result.base_amount == D("1000")

    def test_ivace_07_manual_base_override(self) -> None:
        # Manual base 2000 × 13% = 260 (regardless of the subtotal of 1000).
        result = self.calc.compute_line_taxes(
            taxes=[_make_tax(TaxType.IVACE, rate=D("13"))],
            subtotal=D("1000"),
            detail_quantity=D("1"),
            cabys_code=None,
            monto_total_original=D("1000"),
            ivace_base_override=D("2000"),
        )
        assert result.per_tax[0].amount == D("260")
        assert result.base_amount == D("2000")
        assert result.iva_tax_total == D("260")

    def test_ivarbu_08_factor_times_subtotal(self) -> None:
        # factor 0.13 × subtotal 1000 = 130.
        result = _run(
            self.calc,
            [_make_tax(TaxType.IVARBU, factor=D("0.13"))],
            subtotal=D("1000"),
        )
        assert result.per_tax[0].amount == D("130")
        assert result.iva_tax_total == D("130")

    def test_isec_12_fixed_percentage(self) -> None:
        # 5% × 1000 = 50; ISEC grows the base. Special-fields are required by
        # the DTO validator (§7.5) but the math reads from `tax_rate`.
        result = _run(
            self.calc,
            [
                _make_tax(
                    TaxType.ISEC,
                    rate=D("5"),
                    sf_quantity=D("1"),
                    sf_amount=D("1"),
                )
            ],
            subtotal=D("1000"),
        )
        assert result.per_tax[0].amount == D("50")
        assert result.base_amount == D("1050")

    def test_others_99_uses_updated_base(self) -> None:
        # ISC (10% of 1000 = 100) grows base to 1100; then OTHERS 5% × 1100 = 55.
        taxes = [
            _make_tax(TaxType.ISC, rate=D("10")),
            _make_tax(TaxType.OTHERS, rate=D("5")),
        ]
        result = _run(self.calc, taxes, subtotal=D("1000"))
        # Find the OTHERS row.
        others_rows = [r for r in result.per_tax if r.tax_type_id == TaxType.OTHERS.value]
        assert len(others_rows) == 1
        assert others_rows[0].amount == D("55")
        assert result.base_amount == D("1100")

    def test_royalty_bonus_routes_iva_to_factory_assumed(self) -> None:
        # 13% IVA on 1000 = 130, but routed to factory_assumed when royalty/bonus present.
        result = self.calc.compute_line_taxes(
            taxes=[_make_tax(TaxType.IVA, rate=D("13"))],
            subtotal=D("1000"),
            detail_quantity=D("1"),
            cabys_code=None,
            royalty_bonus_present=True,
            monto_total_original=D("1000"),
        )
        assert result.iva_tax_total == D("0")
        assert result.factory_assumed_tax == D("130")
        assert result.per_tax[0].factory_assumed_amount == D("130")

    def test_royalty_bonus_uses_pre_discount_base_for_iva(self) -> None:
        # §7.1: post-discount subtotal is 900 but pre-discount original is
        # 1000, so 13% IVA must compute on 1000 (=130), not on 900 (=117).
        result = self.calc.compute_line_taxes(
            taxes=[_make_tax(TaxType.IVA, rate=D("13"))],
            subtotal=D("900"),  # discount-eroded subtotal
            detail_quantity=D("1"),
            cabys_code=None,
            royalty_bonus_present=True,
            monto_total_original=D("1000"),
        )
        assert result.iva_tax_total == D("0")
        assert result.factory_assumed_tax == D("130")
        assert result.per_tax[0].amount == D("130")
        assert result.per_tax[0].base_amount == D("1000")

    def test_code_02_uses_pre_discount_base_but_keeps_iva_on_customer(self) -> None:
        # §7.2: code 02 (royalty/bonus VAT-to-customer) — IVA on
        # monto_total_original (=1000), result goes to net_tax (customer pays),
        # NOT to factory_assumed_tax.
        result = self.calc.compute_line_taxes(
            taxes=[_make_tax(TaxType.IVA, rate=D("13"))],
            subtotal=D("900"),
            detail_quantity=D("1"),
            cabys_code=None,
            royalty_bonus_present=False,
            customer_pays_tax_on_original_base=True,
            monto_total_original=D("1000"),
        )
        assert result.iva_tax_total == D("130")
        assert result.factory_assumed_tax == D("0")
        assert result.net_tax == D("130")
        assert result.per_tax[0].base_amount == D("1000")

    def test_royalty_bonus_does_not_reroute_special_taxes(self) -> None:
        # §7.6: royalty/bonus only affects the IVA family. ISC (10% × 1000 =
        # 100) must stay in `other_tax_total` and `net_tax`, never re-route
        # into `factory_assumed_tax`. IVA on the other hand routes correctly.
        result = self.calc.compute_line_taxes(
            taxes=[
                _make_tax(TaxType.ISC, rate=D("10")),
                _make_tax(TaxType.IVA, rate=D("13")),
            ],
            subtotal=D("1000"),
            detail_quantity=D("1"),
            cabys_code=None,
            royalty_bonus_present=True,
            monto_total_original=D("1000"),
        )
        assert result.other_tax_total == D("100")
        # ISC contributes 100 to net_tax; IVA was re-routed to factory_assumed.
        assert result.net_tax == D("100")
        # IVA on pre-discount original 1000 × 13% = 130, routed to factory.
        assert result.factory_assumed_tax == D("130")
        # The ISC row must not carry a factory_assumed_amount.
        isc_rows = [r for r in result.per_tax if r.tax_type_id == TaxType.ISC.value]
        assert isc_rows[0].factory_assumed_amount == D("0")
