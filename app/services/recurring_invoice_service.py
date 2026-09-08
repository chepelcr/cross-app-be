from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from app.models.verticals import RecurringInvoice

logger = logging.getLogger(__name__)

CADENCES = ("weekly", "monthly", "yearly")


def _add_months(value: date, months: int) -> date:
    """Month arithmetic that clamps instead of overflowing.

    The 31st + 1 month is the 30th (or the 28th/29th), not the 1st of the month
    after — a subscription billed on the 31st must not skip February.
    """
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1

    day = value.day
    while day > 1:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, 1)


def next_run_date(cadence: str, from_date: date) -> date:
    if cadence == "weekly":
        return date.fromordinal(from_date.toordinal() + 7)
    if cadence == "yearly":
        return _add_months(from_date, 12)
    if cadence == "monthly":
        return _add_months(from_date, 1)
    raise ValueError(f"Unknown cadence '{cadence}' (expected one of {CADENCES})")


def due_schedules(schedules: List[RecurringInvoice], on: Optional[date] = None) -> List[RecurringInvoice]:
    """Schedules whose next run has arrived.

    Includes anything OVERDUE, not just exactly due: if the scheduler missed a
    day, the customer still expects their invoice.
    """
    on = on or date.today()
    out = []
    for s in schedules:
        if s.deleted_on is not None or s.status != 1:
            continue
        if s.next_run_on is None:
            continue
        due = s.next_run_on if isinstance(s.next_run_on, date) else date.fromisoformat(str(s.next_run_on))
        if due <= on:
            out.append(s)
    return out
