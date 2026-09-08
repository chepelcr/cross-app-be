"""Unit conversion (TSR-161) and recurring cadence (TSR-160)."""
from datetime import date

import pytest

from app.models.verticals import ProductUnit, RecurringInvoice
from app.services.product_unit_service import (
    UnitConversionError,
    to_base_quantity,
    unit_price,
)
from app.services.recurring_invoice_service import due_schedules, next_run_date


def _unit(code, factor, is_base=False, override=None):
    u = ProductUnit(
        product_unit_id=None, product_id="p1", unit_code=code,
        factor_to_base=factor, is_base=is_base, price_override=override,
    )
    u.deleted_on = None
    u.status = 1
    return u


UNITS = [_unit("m", 1, is_base=True), _unit("rollo", 50)]


def test_selling_in_a_larger_unit_converts_inventory():
    assert to_base_quantity(UNITS, "rollo", 2) == 100
    assert to_base_quantity(UNITS, "m", 3) == 3


def test_unknown_unit_is_rejected_rather_than_assumed():
    with pytest.raises(UnitConversionError):
        to_base_quantity(UNITS, "kg", 1)


def test_non_positive_factor_is_rejected():
    """A zero factor would silently zero out every inventory movement."""
    with pytest.raises(UnitConversionError):
        to_base_quantity([_unit("bad", 0)], "bad", 5)


def test_price_scales_by_factor_without_an_override():
    assert unit_price(UNITS, "rollo", 1000) == 50000


def test_price_override_wins():
    """A shop prices a cut metre deliberately; deriving it would lose money."""
    units = [_unit("m", 1, is_base=True), _unit("rollo", 50, override=45000)]
    assert unit_price(units, "rollo", 1000) == 45000


def test_monthly_cadence_clamps_instead_of_overflowing():
    """The 31st + 1 month is the 30th — a subscription must not skip February."""
    assert next_run_date("monthly", date(2026, 1, 31)) == date(2026, 2, 28)
    assert next_run_date("monthly", date(2026, 3, 31)) == date(2026, 4, 30)
    assert next_run_date("monthly", date(2026, 1, 15)) == date(2026, 2, 15)


def test_weekly_and_yearly():
    assert next_run_date("weekly", date(2026, 9, 7)) == date(2026, 9, 14)
    assert next_run_date("yearly", date(2026, 9, 7)) == date(2027, 9, 7)


def test_unknown_cadence_rejected():
    with pytest.raises(ValueError):
        next_run_date("fortnightly", date(2026, 9, 7))


def _schedule(next_run, status=1):
    s = RecurringInvoice(
        recurring_id=None, organization_id="org", name="n",
        cadence="monthly", next_run_on=next_run,
    )
    s.deleted_on = None
    s.status = status
    return s


def test_overdue_schedules_are_included_not_skipped():
    """If the scheduler missed a day the customer still expects the invoice."""
    overdue = _schedule(date(2026, 9, 1))
    today = _schedule(date(2026, 9, 7))
    future = _schedule(date(2026, 10, 1))

    due = due_schedules([overdue, today, future], date(2026, 9, 7))
    assert len(due) == 2


def test_inactive_schedules_are_ignored():
    assert due_schedules([_schedule(date(2026, 9, 1), status=0)], date(2026, 9, 7)) == []
