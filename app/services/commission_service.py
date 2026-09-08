from __future__ import annotations

import logging
from typing import List, Optional

from app.models.verticals import CommissionRule

logger = logging.getLogger(__name__)


def resolve_commission_percent(
    rules: List[CommissionRule],
    staff_user_id: Optional[str],
    product_id: Optional[str],
    category_id: Optional[str],
) -> float:
    """Commission percentage for one sold line.

    Most specific rule wins, in this order:

        1. this staff member + this product
        2. this staff member + this category
        3. this staff member (any product)
        4. this product   (any staff)
        5. this category  (any staff)
        6. org-wide default

    Resolved here rather than in a query so the precedence is readable in one
    place — a scoring expression in SQL would hide exactly the rule people
    argue about when a payout looks wrong.
    """
    def score(rule: CommissionRule) -> Optional[int]:
        if rule.deleted_on is not None or rule.status != 1:
            return None

        staff_match = rule.staff_user_id is not None and rule.staff_user_id == staff_user_id
        staff_any = rule.staff_user_id is None
        if not (staff_match or staff_any):
            return None

        product_match = rule.product_id is not None and rule.product_id == product_id
        category_match = rule.category_id is not None and rule.category_id == category_id

        if rule.product_id is not None and not product_match:
            return None
        if rule.category_id is not None and not category_match:
            return None

        if staff_match and product_match:
            return 6
        if staff_match and category_match:
            return 5
        if staff_match:
            return 4
        if product_match:
            return 3
        if category_match:
            return 2
        return 1

    best: Optional[tuple[int, float]] = None
    for rule in rules:
        s = score(rule)
        if s is None:
            continue
        if best is None or s > best[0]:
            best = (s, float(rule.percent or 0))

    return best[1] if best else 0.0
