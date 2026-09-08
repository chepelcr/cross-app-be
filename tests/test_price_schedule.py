"""Happy-hour price resolution (TSR-158).

Price is authority-critical: the POS resolves schedules locally so it works
offline, but the server re-resolves on submit. These lock the rule both sides
must agree on.
"""
from datetime import datetime, time

from app.models.verticals import PriceSchedule, PriceScheduleItem
from app.services.price_schedule_service import resolve_price, schedule_is_active


def _schedule(**kw) -> PriceSchedule:
    s = PriceSchedule(
        schedule_id=None, organization_id="org", name=kw.get("name", "s"),
        days_of_week=kw.get("days"), start_time=kw.get("start"),
        end_time=kw.get("end"), priority=kw.get("priority", 0),
    )
    s.status = 1
    s.deleted_on = None
    s.items = kw.get("items", [])
    return s


def _item(**kw) -> PriceScheduleItem:
    return PriceScheduleItem(
        item_id=None, schedule_id=None,
        product_id=kw.get("product_id"), category_id=kw.get("category_id"),
        price=kw.get("price"), discount_percent=kw.get("discount_percent"),
    )


WED_1800 = datetime(2026, 9, 9, 18, 0)   # a Wednesday


def test_window_inside_the_day():
    s = _schedule(start=time(17, 0), end=time(20, 0))
    assert schedule_is_active(s, WED_1800) is True
    assert schedule_is_active(s, datetime(2026, 9, 9, 21, 0)) is False


def test_window_wrapping_midnight():
    """22:00–02:00 is the normal shape of a happy hour; a naive start<=now<=end
    comparison would never match it."""
    s = _schedule(start=time(22, 0), end=time(2, 0))
    assert schedule_is_active(s, datetime(2026, 9, 9, 23, 30)) is True
    assert schedule_is_active(s, datetime(2026, 9, 10, 1, 0)) is True
    assert schedule_is_active(s, datetime(2026, 9, 9, 12, 0)) is False


def test_day_filter():
    s = _schedule(days=[1, 2], start=time(0, 0), end=time(23, 59))
    assert schedule_is_active(s, WED_1800) is False       # Wednesday = 3
    assert schedule_is_active(s, datetime(2026, 9, 7, 18, 0)) is True  # Monday


def test_flat_price_wins_over_base():
    s = _schedule(start=time(17, 0), end=time(20, 0),
                  items=[_item(product_id="p1", price=800)])
    assert resolve_price([s], "p1", None, 1000, WED_1800) == 800


def test_percentage_discount_applies():
    s = _schedule(start=time(17, 0), end=time(20, 0),
                  items=[_item(product_id="p1", discount_percent=25)])
    assert resolve_price([s], "p1", None, 1000, WED_1800) == 750


def test_highest_priority_wins():
    low = _schedule(priority=1, start=time(0, 0), end=time(23, 59),
                    items=[_item(product_id="p1", price=900)])
    high = _schedule(priority=5, start=time(0, 0), end=time(23, 59),
                     items=[_item(product_id="p1", price=700)])
    assert resolve_price([low, high], "p1", None, 1000, WED_1800) == 700


def test_product_item_beats_category_item():
    s = _schedule(start=time(0, 0), end=time(23, 59), items=[
        _item(category_id="c1", price=900),
        _item(product_id="p1", price=800),
    ])
    assert resolve_price([s], "p1", "c1", 1000, WED_1800) == 800


def test_schedule_never_raises_the_price():
    """A misconfigured 'discount' above catalog price must not become a surcharge."""
    s = _schedule(start=time(0, 0), end=time(23, 59),
                  items=[_item(product_id="p1", price=5000)])
    assert resolve_price([s], "p1", None, 1000, WED_1800) == 1000


def test_inactive_schedule_is_ignored():
    s = _schedule(start=time(0, 0), end=time(23, 59),
                  items=[_item(product_id="p1", price=100)])
    s.status = 0
    assert resolve_price([s], "p1", None, 1000, WED_1800) == 1000


def test_no_match_returns_base_price():
    assert resolve_price([], "p1", None, 1000, WED_1800) == 1000
