"""FEFO lot picking (TSR-159) and commission precedence (TSR-162)."""
from datetime import date, timedelta

import pytest

from app.models.verticals import CommissionRule, ProductLot
from app.services.commission_service import resolve_commission_percent
from app.services.lot_service import (
    LotExpiredError,
    expiry_warning,
    pick_lot,
    sellable_lots,
)

TODAY = date(2026, 9, 7)


def _lot(code, expires, qty=10):
    lot = ProductLot(
        lot_id=None, organization_id="org", product_id="p1",
        lot_code=code, expires_on=expires, quantity=qty,
    )
    lot.deleted_on = None
    lot.status = 1
    return lot


def test_fefo_picks_the_soonest_expiry_not_the_oldest_arrival():
    lots = [
        _lot("late", TODAY + timedelta(days=90)),
        _lot("soon", TODAY + timedelta(days=5)),
    ]
    assert pick_lot(lots, TODAY).lot_code == "soon"


def test_expired_lots_are_excluded():
    lots = [_lot("old", TODAY - timedelta(days=1)), _lot("good", TODAY + timedelta(days=5))]
    assert [l.lot_code for l in sellable_lots(lots, TODAY)] == ["good"]


def test_a_lot_expiring_today_is_still_sellable():
    assert pick_lot([_lot("today", TODAY)], TODAY).lot_code == "today"


def test_depleted_lots_are_excluded():
    lots = [_lot("empty", TODAY + timedelta(days=5), qty=0), _lot("stock", TODAY + timedelta(days=9))]
    assert [l.lot_code for l in sellable_lots(lots, TODAY)] == ["stock"]


def test_undated_lot_sorts_last():
    """Undated stock must not jump ahead of something about to expire."""
    lots = [_lot("undated", None), _lot("soon", TODAY + timedelta(days=3))]
    assert [l.lot_code for l in sellable_lots(lots, TODAY)] == ["soon", "undated"]


def test_nothing_sellable_raises_rather_than_returning_expired_stock():
    with pytest.raises(LotExpiredError):
        pick_lot([_lot("old", TODAY - timedelta(days=1))], TODAY)


def test_expiry_warning_only_inside_the_window():
    assert expiry_warning(_lot("a", TODAY + timedelta(days=10)), TODAY) == 10
    assert expiry_warning(_lot("b", TODAY + timedelta(days=90)), TODAY) is None
    assert expiry_warning(_lot("c", None), TODAY) is None


def test_expiring_today_warns_with_zero_not_none():
    """0 means 'expires today' — a warning, not the absence of one."""
    assert expiry_warning(_lot("d", TODAY), TODAY) == 0


def _rule(percent, staff=None, product=None, category=None):
    r = CommissionRule(
        rule_id=None, organization_id="org", staff_user_id=staff,
        product_id=product, category_id=category, percent=percent,
    )
    r.deleted_on = None
    r.status = 1
    return r


def test_commission_most_specific_rule_wins():
    rules = [
        _rule(5),                                   # org-wide
        _rule(8, staff="u1"),                       # staff-wide
        _rule(12, staff="u1", product="p1"),        # staff + product
    ]
    assert resolve_commission_percent(rules, "u1", "p1", "c1") == 12


def test_commission_falls_back_through_the_chain():
    rules = [_rule(5), _rule(8, staff="u1")]
    assert resolve_commission_percent(rules, "u1", "p9", "c9") == 8
    assert resolve_commission_percent(rules, "u2", "p9", "c9") == 5


def test_rule_for_another_staff_member_does_not_apply():
    rules = [_rule(20, staff="someone-else", product="p1")]
    assert resolve_commission_percent(rules, "u1", "p1", "c1") == 0.0


def test_no_rules_means_no_commission():
    assert resolve_commission_percent([], "u1", "p1", "c1") == 0.0
