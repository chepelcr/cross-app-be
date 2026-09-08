from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

from app.models.verticals import ProductLot

logger = logging.getLogger(__name__)

#: Lots expiring inside this window are flagged, not blocked — the pharmacist
#: decides whether to sell short-dated stock, but should not do it unknowingly.
DEFAULT_WARN_DAYS = 30


class LotExpiredError(ValueError):
    """Raised when the only sellable lot is already past its expiry date."""


def _as_date(value) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def sellable_lots(lots: List[ProductLot], on: Optional[date] = None) -> List[ProductLot]:
    """Lots with stock that have not expired, in FEFO order.

    First Expiry, First Out — not FIFO. For anything with a shelf life the
    date that matters is when it goes bad, not when it arrived.

    A lot with no expiry sorts last: undated stock should not jump ahead of
    something that is about to expire.
    """
    on = on or date.today()
    live = [
        lot
        for lot in lots
        if lot.deleted_on is None
        and float(lot.quantity or 0) > 0
        and (_as_date(lot.expires_on) is None or _as_date(lot.expires_on) >= on)
    ]
    return sorted(
        live,
        key=lambda lot: (_as_date(lot.expires_on) is None, _as_date(lot.expires_on) or date.max),
    )


def pick_lot(lots: List[ProductLot], on: Optional[date] = None) -> ProductLot:
    """The lot a till should default to. Raises when nothing is sellable."""
    candidates = sellable_lots(lots, on)
    if not candidates:
        raise LotExpiredError("No sellable lot: all stock is expired or depleted")
    return candidates[0]


def expiry_warning(
    lot: ProductLot, on: Optional[date] = None, warn_days: int = DEFAULT_WARN_DAYS
) -> Optional[int]:
    """Days until this lot expires when that is inside the warning window.

    Returns None when the lot is undated or comfortably in date — so a falsy
    result means "nothing to say", and 0 means "expires today", which is a
    warning rather than an absence of one.
    """
    expires = _as_date(lot.expires_on)
    if expires is None:
        return None
    on = on or date.today()
    remaining = (expires - on).days
    return remaining if remaining <= warn_days else None
