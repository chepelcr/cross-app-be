"""End-to-end orchestration tests for `LineCalculator`.

Covers a representative scenario combining a royalty discount + IVA + ISEBEC.
"""
from __future__ import annotations

from decimal import Decimal

from app.dtos.requests.product_request_dto import (
    ProductDiscountDTO,
    ProductTaxDTO,
    TaxAmountDTO,
    TaxRateDTO,
    TaxSpecialFieldsDTO,
)
from app.enums.hacienda_codes import CabysSpecialPrefix, DiscountType, TaxRateCode, TaxType
from app.services.line_calculation_service import LineCalculator, LineInput

D = Decimal


class TestLineCalculator:
    def setup_method(self) -> None:
        self.calc = LineCalculator()

    def test_plain_iva_only(self) -> None:
        # 1000 net, 13% IVA, no discounts → sale 1130.
        line = LineInput(
            price=D("1000"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.IVA.value,
                    tax_rate=TaxRateDTO(
                        percentage=13.0, code=TaxRateCode.GENERAL_13.value
                    ),
                )
            ],
        )
        result = self.calc.compute(line)
        assert result.total_amount == D("1000")
        assert result.subtotal == D("1000")
        assert result.sale_price == D("1130")
        assert result.tax.iva_tax_total == D("130")
        assert result.tax.factory_assumed_tax == D("0")

    def test_royalty_discount_routes_iva_to_factory_assumed(self) -> None:
        # 1000 net, 10% royalty (01) -> subtotal 900. Per §7.1, IVA is computed
        # on monto_total_original (=1000) × 13% = 130 (NOT on the eroded 900),
        # routed to factory_assumed_tax; sale price stays at the post-discount
        # subtotal because the customer never pays the factory-assumed tax.
        line = LineInput(
            price=D("1000"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[
                ProductDiscountDTO(
                    discount_type_id=DiscountType.ROYALTY.value,
                    percentage=10.0,
                )
            ],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.IVA.value,
                    tax_rate=TaxRateDTO(
                        percentage=13.0, code=TaxRateCode.GENERAL_13.value
                    ),
                )
            ],
        )
        result = self.calc.compute(line)
        assert result.subtotal == D("900")
        assert result.tax.iva_tax_total == D("0")
        assert result.tax.factory_assumed_tax == D("130")
        assert result.sale_price == D("900")

    def test_combined_isebec_beverage_plus_iva(self) -> None:
        # ISEBEC on a beverage: detail (1) × CantidadUM (2) × (unit 50 / vol 3)
        # = 33.33333. It grows the IVA base to 1033.33333, so IVA is 134.33333.
        # ISEBEC itself is issuer-assumed (-476), so it leaves `net_tax`: the
        # customer pays only the IVA, and sale_price = 1000 + 134.33333.
        line = LineInput(
            price=D("1000"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.ISEBEC.value,
                    special_fields=TaxSpecialFieldsDTO(
                        quantity=2.0,
                        volume_consumption=3.0,
                        tax_amount=TaxAmountDTO(id="ta", amount=50.0),
                    ),
                ),
                ProductTaxDTO(
                    tax_type_id=TaxType.IVA.value,
                    tax_rate=TaxRateDTO(
                        percentage=13.0, code=TaxRateCode.GENERAL_13.value
                    ),
                ),
            ],
        )
        # Any CABYS that is not toilet soap takes the volume formula.
        result = self.calc.compute(line, cabys_code="9999")
        assert result.tax.factory_assumed_tax == D("33.33333")
        assert result.tax.base_amount == D("1033.33333")
        assert result.tax.iva_tax_total == D("134.33333")
        assert result.tax.net_tax == D("134.33333")
        assert result.sale_price == D("1134.33333")

    def test_isebec_toilet_soap_branch_via_cabys_prefix(self) -> None:
        # Toilet soap prices per GRAM: detail (1) × volume 2 g × unit 10 = 20,
        # and the issuer absorbs it, so the customer pays nothing on top.
        line = LineInput(
            price=D("500"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.ISEBEC.value,
                    special_fields=TaxSpecialFieldsDTO(
                        quantity=2.0,
                        volume_consumption=2.0,
                        tax_amount=TaxAmountDTO(id="ta", amount=10.0),
                    ),
                )
            ],
        )
        result = self.calc.compute(
            line,
            cabys_code=CabysSpecialPrefix.ISEBEC_TOILET_SOAP.value + "01",
        )
        assert result.tax.factory_assumed_tax == D("20")
        assert result.tax.net_tax == D("0")
        assert result.sale_price == D("500")

    def test_royalty_plus_isc_plus_iva_end_to_end(self) -> None:
        # §7.1 + §7.6 end-to-end:
        # 1000 net, 10% royalty (code 01) -> subtotal 900.
        # ISC 10% on subtotal 900 = 90, grows base to 990; net_tax += 90.
        # IVA must use monto_total_original (=1000) × 13% = 130, routed to
        # factory_assumed_tax (NOT net_tax).
        line = LineInput(
            price=D("1000"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[
                ProductDiscountDTO(
                    discount_type_id=DiscountType.ROYALTY.value,
                    percentage=10.0,
                )
            ],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.ISC.value,
                    tax_rate=TaxRateDTO(percentage=10.0),
                ),
                ProductTaxDTO(
                    tax_type_id=TaxType.IVA.value,
                    tax_rate=TaxRateDTO(
                        percentage=13.0, code=TaxRateCode.GENERAL_13.value
                    ),
                ),
            ],
        )
        result = self.calc.compute(line)
        assert result.subtotal == D("900")
        assert result.tax.other_tax_total == D("90")
        assert result.tax.iva_tax_total == D("0")
        assert result.tax.factory_assumed_tax == D("130")
        # net_tax = ISC (90) + nothing from IVA (factory-routed)
        assert result.tax.net_tax == D("90")
        # sale_price = post-discount subtotal (900) + net_tax (90) = 990
        assert result.sale_price == D("990")

    def test_code_02_discount_is_an_ordinary_discount(self) -> None:
        # 1000 net, 10% code-02 discount -> subtotal 900, IVA 13% × 900 = 117,
        # paid by the customer. The un-eroded reading of nature 02 is gone —
        # Hacienda rejects it with -45 and -454 together; see the discount
        # service docstring.
        line = LineInput(
            price=D("1000"),
            quantity=D("1"),
            is_packaged=False,
            detail_quantity=D("1"),
            discounts=[
                ProductDiscountDTO(
                    discount_type_id=DiscountType.ROYALTY_BONUS_VAT_CUSTOMER.value,
                    percentage=10.0,
                )
            ],
            taxes=[
                ProductTaxDTO(
                    tax_type_id=TaxType.IVA.value,
                    tax_rate=TaxRateDTO(
                        percentage=13.0, code=TaxRateCode.GENERAL_13.value
                    ),
                )
            ],
        )
        result = self.calc.compute(line)
        assert result.subtotal == D("900")
        assert result.tax.iva_tax_total == D("117")
        assert result.tax.factory_assumed_tax == D("0")
        assert result.tax.net_tax == D("117")
        assert result.sale_price == D("1017")

    def test_packaged_line_uses_quantity_for_total(self) -> None:
        # is_packaged True + price 100 × qty 5 = 500 total before discounts/taxes.
        line = LineInput(
            price=D("100"),
            quantity=D("5"),
            is_packaged=True,
            detail_quantity=D("5"),
            discounts=[],
            taxes=[],
        )
        result = self.calc.compute(line)
        assert result.total_amount == D("500")
        assert result.subtotal == D("500")
        assert result.sale_price == D("500")
