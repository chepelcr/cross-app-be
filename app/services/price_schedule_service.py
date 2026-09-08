from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time
from typing import List, Optional, Sequence

from app.models.verticals import PriceSchedule, PriceScheduleItem

logger = logging.getLogger(__name__)


def schedule_is_active(schedule: PriceSchedule, at: datetime) -> bool:
    """Is this schedule in force at `at`?

    Windows that wrap midnight (22:00–02:00, the usual happy hour) are handled
    explicitly: a naive `start <= now <= end` comparison would never match one.
    """
    days: Optional[Sequence[int]] = schedule.days_of_week or None
    if days:
        # ISO weekday: Monday = 1 … Sunday = 7.
        if at.isoweekday() not in [int(d) for d in days]:
            return False

    start: Optional[time] = schedule.start_time
    end: Optional[time] = schedule.end_time
    if start is None or end is None:
        return True

    now = at.time()
    if start <= end:
        return start <= now <= end
    # Wraps midnight.
    return now >= start or now <= end


def resolve_price(
    schedules: List[PriceSchedule],
    product_id: str,
    category_id: Optional[str],
    base_price: float,
    at: Optional[datetime] = None,
) -> float:
    """Price for a product right now, honouring the active schedules.

    Highest `priority` wins; a product-specific item beats a category one within
    the same schedule. Returns `base_price` when nothing applies.

    **This is the authority.** The POS runs the same rule locally so it works
    offline, but the server re-resolves on submit: a stale or tampered client
    clock must never set the price on a fiscal document.
    """
    at = at or datetime.now()
    best: Optional[tuple[int, float]] = None

    for schedule in schedules:
        if schedule.deleted_on is not None or schedule.status != 1:
            continue
        if not schedule_is_active(schedule, at):
            continue

        product_item: Optional[PriceScheduleItem] = None
        category_item: Optional[PriceScheduleItem] = None
        for item in schedule.items or []:
            if item.product_id and item.product_id == product_id:
                product_item = item
            elif item.category_id and category_id and item.category_id == category_id:
                category_item = item

        item = product_item or category_item
        if item is None:
            continue

        if item.price is not None:
            candidate = float(item.price)
        elif item.discount_percent is not None:
            candidate = base_price * (1 - float(item.discount_percent) / 100)
        else:
            continue

        # Never let a schedule raise the price above catalog — a "discount"
        # that costs more is a misconfiguration, not an offer.
        candidate = min(candidate, base_price)
        priority = schedule.priority or 0

        if best is None or priority > best[0]:
            best = (priority, candidate)

    return best[1] if best else base_price
