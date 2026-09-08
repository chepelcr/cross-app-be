"""Order Status Enum."""

# `can_transition` annotates `current: str | None`. PEP 604 unions are only
# valid as *runtime* expressions on Python 3.10+, and this service deploys on
# the python3.9 Lambda runtime — so without this import the annotation is
# evaluated at def time and raises
#   TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
# at import. That crashed every cd-backend invocation (orders, branches,
# terminals, sessions, assignments), which took the whole POS down: a cashier
# could not load a puesto, so no shift could start and no document could be
# created. Postponed evaluation keeps annotations as strings, so this is safe
# on 3.9 and stays correct once the runtime moves.
from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """Order status values.

    QUOTE is the proforma state (TSR-156). A cotización is an order in an early
    status, **not** a separate document type — which is why converting one to a
    firm pedido is a status change and nothing else, and why "Facturar pedido"
    needs no special case for it.
    """

    QUOTE = "quote"
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


#: Numeric codes the FE sends on a status PATCH. QUOTE sits at 0 because it
#: precedes `pending`: a quote has not been placed yet.
ORDER_STATUS_CODES: dict[str, int] = {
    OrderStatus.QUOTE.value: 0,
    OrderStatus.PENDING.value: 1,
    OrderStatus.PROCESSING.value: 2,
    OrderStatus.SHIPPED.value: 3,
    OrderStatus.DELIVERED.value: 4,
    OrderStatus.CANCELLED.value: 5,
}

#: Where each status may go next.
#:
#: A quote may only be approved into `pending` or cancelled — it must NOT jump
#: straight to `delivered`, because that would let an unapproved cotización be
#: invoiced as though the customer had agreed to it.
ORDER_STATUS_TRANSITIONS: dict[str, tuple[str, ...]] = {
    OrderStatus.QUOTE.value: (OrderStatus.PENDING.value, OrderStatus.CANCELLED.value),
    OrderStatus.PENDING.value: (
        OrderStatus.PROCESSING.value,
        OrderStatus.SHIPPED.value,
        OrderStatus.DELIVERED.value,
        OrderStatus.CANCELLED.value,
    ),
    OrderStatus.PROCESSING.value: (
        OrderStatus.SHIPPED.value,
        OrderStatus.DELIVERED.value,
        OrderStatus.CANCELLED.value,
    ),
    OrderStatus.SHIPPED.value: (OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value),
    # Terminal states.
    OrderStatus.DELIVERED.value: (),
    OrderStatus.CANCELLED.value: (),
}


def can_transition(current: str | None, target: str) -> bool:
    """May an order move from `current` to `target`?

    An unknown current status is treated as `pending` — legacy rows predate the
    vocabulary and should not be frozen by it.
    """
    if current == target:
        return True
    key = current if current in ORDER_STATUS_TRANSITIONS else OrderStatus.PENDING.value
    return target in ORDER_STATUS_TRANSITIONS[key]
