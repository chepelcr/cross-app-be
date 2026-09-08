"""Manual-order line arithmetic (TSR-152).

The single rule these lock in: **the client's numbers are never authoritative**.
A pedido captured in the POS may be replayed from an offline outbox, edited by
hand, or simply wrong — and the order it produces can later be turned into a
fiscal document, so a bad tax figure would not stay harmless.
"""
from app.dtos.requests.manual_order_dto import ManualOrderLineDTO
from app.services.order_service import _line_amounts


def test_flat_line_recomputes_total_and_ignores_client_figure():
    """A flat line has no structure to derive tax from, so the caller's tax
    stands — but the total is still recomputed, not trusted."""
    line = ManualOrderLineDTO(
        line_number=1, description="Cafe molido 500 g", quantity=10,
        unit_price=3500, discount=3500, tax=4095,
        line_total=999_999,  # deliberately absurd
    )
    subtotal, discount, tax, total = _line_amounts(line)

    assert subtotal == 31_500.0
    assert discount == 3_500.0
    assert tax == 4_095.0
    assert total == 35_595.0  # not 999_999


def test_structured_line_derives_tax_through_the_shared_calculator():
    """With a structured breakdown the line goes through the same
    LineCalculator a sale uses, so a pedido and the factura it becomes agree."""
    line = ManualOrderLineDTO(
        line_number=1, description="Cafe molido 500 g", quantity=10,
        unit_price=3500, discount=0, tax=0, line_total=0,
        cabys="0161010150000",
        taxes=[{"code": "01", "rate_code": "08", "rate": 13}],
    )
    subtotal, discount, tax, total = _line_amounts(line)

    assert subtotal == 35_000.0
    assert discount == 0.0
    assert round(tax, 2) == 4_550.00      # 13% derived, not sent
    assert round(total, 2) == 39_550.00


def test_discount_applies_before_tax_hacienda_cascade():
    """Tax is charged on the DISCOUNTED base — the cascade, not a sum of
    percentages."""
    line = ManualOrderLineDTO(
        line_number=1, description="Cafe molido 500 g", quantity=10,
        unit_price=3500, discount=0, tax=0, line_total=0,
        cabys="0161010150000",
        taxes=[{"code": "01", "rate_code": "08", "rate": 13}],
        discounts=[{"code": "99", "nature": "Promo setiembre", "percentage": 10}],
    )
    subtotal, discount, tax, total = _line_amounts(line)

    assert discount == 3_500.0            # 10% of 35 000
    assert subtotal == 31_500.0
    assert round(tax, 2) == 4_095.00      # 13% of 31 500, not of 35 000
    assert round(total, 2) == 35_595.00


def test_exempt_line_stays_exempt():
    """A 0% rate must produce zero tax rather than falling back to the general
    rate — this is what makes a mixed-rate combo safe to explode."""
    line = ManualOrderLineDTO(
        line_number=1, description="Canasta basica", quantity=2,
        unit_price=1000, discount=0, tax=0, line_total=0,
        taxes=[{"code": "01", "rate_code": "01", "rate": 0}],
    )
    subtotal, _discount, tax, total = _line_amounts(line)

    assert subtotal == 2_000.0
    assert tax == 0.0
    assert total == 2_000.0
