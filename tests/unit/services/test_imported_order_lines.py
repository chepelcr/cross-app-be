"""Imported-order line rebuild: header-discount allocation + line recompute.

These cover the seam between a customer's spreadsheet and a billable pedido.
The spreadsheet has no tax structure and — in practice — often no line-level
discounts either, so the import has to derive both. Getting either wrong is
silent: the order looks right and the invoice built from it overcharges.

The helpers under test are pure, so they are loaded out of `order_service`
without importing the module (which pulls in SQLAlchemy, boto3 and S3).
"""
from __future__ import annotations

import ast
import pathlib
from decimal import ROUND_HALF_UP, Decimal

import pytest

from app.dtos.requests.product_request_dto import ProductDiscountDTO, ProductTaxDTO
from app.enums.hacienda_codes import DiscountType
from app.services.line_calculation_service import LineCalculator, LineInput

D = Decimal

_HELPERS = {
    "_round_money",
    "_normalize_tax_row",
    "_normalize_discount_row",
    "_imported_line_discounts",
    "_imported_line_taxes",
    "_imported_line_net_price",
    "_allocate_header_discount",
    "_line_input_from_structured",
    "_recompute_imported_line",
    "_resum_order_totals",
}


def _load_helpers() -> dict:
    """Exec just the pure helpers from `order_service`, with their deps bound."""
    source = pathlib.Path("app/services/order_service.py").read_text()
    tree = ast.parse(source)
    module = ast.Module(
        body=[
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in _HELPERS
        ],
        type_ignores=[],
    )
    namespace = {
        "Decimal": Decimal,
        "ROUND_HALF_UP": ROUND_HALF_UP,
        "DiscountType": DiscountType,
        "ProductDiscountDTO": ProductDiscountDTO,
        "ProductTaxDTO": ProductTaxDTO,
        "LineCalculator": LineCalculator,
        "LineInput": LineInput,
    }
    exec(compile(module, "order_service_helpers", "exec"), namespace)
    return namespace


helpers = _load_helpers()


class Row:
    """Minimal stand-in for a parsed spreadsheet line / an `OrderLine`."""

    def __init__(self, **fields) -> None:
        self.__dict__.update(fields)


def _parsed_line(line_number: int, unit_price: float, qty: int, discount: float = 0):
    return Row(
        line_number=line_number,
        unit_price=unit_price,
        quantity_ordered=qty,
        units_ordered=qty,
        discount=discount,
    )


class TestHeaderDiscountAllocation:
    """Real chain spreadsheets leave every line at 0 and total the discount."""

    def test_allocates_in_proportion_to_line_gross(self) -> None:
        parsed = Row(
            discounts=1000.0,
            lines=[_parsed_line(1, 100.0, 10), _parsed_line(2, 200.0, 15)],
        )
        allocated = helpers["_allocate_header_discount"](parsed)
        # Gross is 1 000 and 3 000, so 25% / 75% of the 1 000 discount.
        assert allocated[1] == pytest.approx(250.0)
        assert allocated[2] == pytest.approx(750.0)

    def test_allocation_sums_back_to_the_header_exactly(self) -> None:
        # Three equal lines cannot be split evenly at 5 dp; the rounding
        # remainder has to land somewhere or the order stops reconciling.
        parsed = Row(
            discounts=10.0,
            lines=[_parsed_line(i, 10.0, 1) for i in range(1, 4)],
        )
        allocated = helpers["_allocate_header_discount"](parsed)
        assert sum(D(str(v)) for v in allocated.values()) == D("10")

    def test_lines_with_their_own_discounts_are_left_alone(self) -> None:
        # A spreadsheet that fills the column in is authoritative; allocating on
        # top of it would double-discount the order.
        parsed = Row(
            discounts=1000.0,
            lines=[_parsed_line(1, 100.0, 10, discount=50), _parsed_line(2, 200.0, 15)],
        )
        assert helpers["_allocate_header_discount"](parsed) == {}

    def test_header_discount_larger_than_the_order_is_capped(self) -> None:
        # Bad data, not a 100% discount — capping keeps a line from going
        # negative and turning into an invoice that pays the customer.
        parsed = Row(discounts=100.0, lines=[_parsed_line(1, 10.0, 1)])
        allocated = helpers["_allocate_header_discount"](parsed)
        assert sum(D(str(v)) for v in allocated.values()) == D("10")

    def test_no_header_discount_allocates_nothing(self) -> None:
        parsed = Row(discounts=0, lines=[_parsed_line(1, 10.0, 1)])
        assert helpers["_allocate_header_discount"](parsed) == {}


class TestImportedLineRecompute:
    def _line(self, **overrides):
        base = dict(
            quantity_ordered=10,
            units_ordered=10,
            unit_price=1000.0,
            net_price=1000.0,
            cabys=None,
            discount=250.0,
            tax=0.0,
            line_total=0.0,
            discounts=helpers["_imported_line_discounts"](250.0),
            taxes=[
                {
                    "tax_type_id": "01",
                    "tax_rate": {"id": "r", "percentage": 13.0, "code": "08"},
                }
            ],
        )
        base.update(overrides)
        return Row(**base)

    def test_recomputes_over_the_order_quantity(self) -> None:
        line = self._line()
        helpers["_recompute_imported_line"](line)
        # 10 x 1 000 = 10 000 gross, less 250, taxed at 13%.
        assert line.discount == pytest.approx(250.0)
        assert line.tax == pytest.approx(9750 * 0.13)
        assert line.line_total == pytest.approx(9750 * 1.13)

    def test_import_discount_is_commercial_not_royalty(self) -> None:
        """07, never 01/03 — the difference is who owes the IVA.

        Natures 01 and 03 route the line's IVA into
        `ImpuestoAsumidoEmisorFabrica`, so mis-typing a supplier's trade
        discount as one of them would make the issuer absorb tax the customer
        actually pays.
        """
        rows = helpers["_imported_line_discounts"](250.0)
        assert rows[0]["discount_type_id"] == DiscountType.COMMERCIAL.value
        assert rows[0]["reason"] is None

    def test_zero_discount_produces_no_discount_row(self) -> None:
        assert helpers["_imported_line_discounts"](0) is None

    def test_line_without_structured_detail_is_untouched(self) -> None:
        """Nothing to derive a rate from — the customer's figures stand."""
        line = self._line(discounts=None, taxes=None, tax=3.0, line_total=497.0)
        helpers["_recompute_imported_line"](line)
        assert line.tax == 3.0
        assert line.line_total == 497.0

    def test_product_taxes_are_copied_without_their_amounts(self) -> None:
        """The product's own `amount` was computed against the PRODUCT's price.

        Carrying it onto the line would assert a figure that has nothing to do
        with the order quantity; `_recompute_imported_line` derives the real one.
        """
        product = Row(taxes=[{"tax_type_id": "01", "amount": 42.0}])
        assert helpers["_imported_line_taxes"](product) == [{"tax_type_id": "01"}]

    def test_net_price_prefers_the_catalog_over_the_spreadsheet(self) -> None:
        parsed = _parsed_line(1, 900.0, 1)
        assert helpers["_imported_line_net_price"](parsed, Row(unit_price=1000.0)) == 1000.0
        assert helpers["_imported_line_net_price"](parsed, Row(unit_price=None)) == 900.0
        assert helpers["_imported_line_net_price"](parsed, Row(unit_price=0)) == 900.0


class TestOrderTotals:
    def test_totals_are_summed_from_the_lines(self) -> None:
        """The header the chain sent is not what the invoice will carry."""
        order = Row(
            lines=[
                Row(unit_price=100.0, quantity_ordered=10, units_ordered=10,
                    discount=50.0, tax=123.5),
                Row(unit_price=200.0, quantity_ordered=5, units_ordered=5,
                    discount=0.0, tax=130.0),
            ],
            subtotal=0, discounts=0, net_total=0, taxes=0, grand_total=0,
            line_count=0, total_quantities=0,
        )
        helpers["_resum_order_totals"](order)
        assert order.subtotal == pytest.approx(2000.0)
        assert order.discounts == pytest.approx(50.0)
        assert order.net_total == pytest.approx(1950.0)
        assert order.taxes == pytest.approx(253.5)
        assert order.grand_total == pytest.approx(2203.5)
        assert order.line_count == 2
        assert order.total_quantities == 15


class TestLegacyRowNormalization:
    """Two spellings of the same column had to be readable by one reader.

    Manual orders persisted the request shape (`code` / `rate` / `nature`);
    imported orders persisted the canonical `ProductTaxDTO` dump. New writes are
    all canonical, but the older rows are still in the database — and they are
    exactly the ones a backfill exists to repair, so it has to read them.
    """

    def test_canonical_tax_row_passes_through_untouched(self) -> None:
        row = {"tax_type_id": "01", "tax_rate": {"percentage": 13.0}}
        assert helpers["_normalize_tax_row"](row) is row

    def test_legacy_tax_row_is_translated(self) -> None:
        row = {"code": "01", "rate": 13.0, "rate_code": "08"}
        assert helpers["_normalize_tax_row"](row) == {
            "tax_type_id": "01",
            "tax_rate": {"id": "08", "percentage": 13.0, "code": "08"},
        }

    def test_legacy_tax_row_keeps_special_fields(self) -> None:
        special = {"quantity": 0.355, "volume_consumption": 0.355}
        row = {"code": "05", "special_fields": special}
        translated = helpers["_normalize_tax_row"](row)
        assert translated["tax_type_id"] == "05"
        assert translated["special_fields"] == special

    def test_legacy_discount_row_is_translated(self) -> None:
        row = {"code": "07", "nature": "trade", "amount": 250.0}
        assert helpers["_normalize_discount_row"](row) == {
            "discount_type_id": "07",
            "reason": "trade",
            "percentage": None,
            "amount": 250.0,
            "is_amount": True,
        }
