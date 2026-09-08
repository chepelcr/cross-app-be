"""Excel-imported lines carry the same structure as POS-captured ones (TSR-152).

The customer's spreadsheet has a discount AMOUNT but no discount TYPE, and no
tax structure at all — only totals. These helpers fill both in so an imported
order and a manual one are equally complete, and either can be billed later
without inventing a rate.
"""
from app.enums.hacienda_codes import (
    FACTORY_ASSUMED_DISCOUNT_NATURES,
    DiscountType,
)
from app.services.order_service import (
    _imported_line_discounts,
    _imported_line_taxes,
)


class _FakeProduct:
    def __init__(self, taxes=None):
        self.taxes = taxes


def test_discount_becomes_commercial_not_other():
    """07 (Comercial), not 99 (Otros): it is the honest reading of a supplier
    trade discount, and unlike 99 it needs no free-text reason."""
    out = _imported_line_discounts(3500)

    assert out is not None
    assert len(out) == 1
    assert out[0]["discount_type_id"] == DiscountType.COMMERCIAL.value == "07"
    assert out[0]["is_amount"] is True
    assert out[0]["amount"] == 3500.0
    assert out[0]["reason"] is None


def test_commercial_discount_does_not_reroute_iva_to_the_factory():
    """Nota 20: only 01 (regalía) and 03 (bonificación) move IVA into
    ImpuestoAsumidoEmisorFabrica. A commercial discount must stay a plain
    price reduction, or every imported order would misreport its tax."""
    assert DiscountType.COMMERCIAL.value not in FACTORY_ASSUMED_DISCOUNT_NATURES
    assert DiscountType.ROYALTY.value in FACTORY_ASSUMED_DISCOUNT_NATURES
    assert DiscountType.BONUS.value in FACTORY_ASSUMED_DISCOUNT_NATURES


def test_no_discount_produces_no_structure():
    """An absent discount stays absent — not a zero-amount row that would show
    up as a discount in the UI and on the printed ticket."""
    assert _imported_line_discounts(0) is None
    assert _imported_line_discounts(None) is None


def test_taxes_are_copied_from_the_product():
    """The stored product JSONB is already ProductTaxDTO-shaped, so it is
    copied rather than re-derived."""
    product = _FakeProduct(
        taxes=[{"tax_type_id": "01", "tax_rate": {"id": "8", "percentage": 13.0}, "amount": 637.0}]
    )
    out = _imported_line_taxes(product)

    assert out is not None
    assert out[0]["tax_type_id"] == "01"
    assert out[0]["tax_rate"]["percentage"] == 13.0


def test_taxes_are_a_copy_not_a_shared_reference():
    """Mutating the line must not reach back into the product row."""
    original = [{"tax_type_id": "01", "amount": 100.0}]
    product = _FakeProduct(taxes=original)

    out = _imported_line_taxes(product)
    out[0]["amount"] = 999.0

    assert original[0]["amount"] == 100.0


def test_product_without_taxes_yields_none():
    assert _imported_line_taxes(_FakeProduct(taxes=None)) is None
    assert _imported_line_taxes(_FakeProduct(taxes=[])) is None
