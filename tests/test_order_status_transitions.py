"""Order status transitions, and the proforma guard (TSR-156).

A cotización is an order in an early status, not a separate document type. The
rule that matters: a quote must be APPROVED before it can be delivered, or an
unapproved proforma could be invoiced as though the customer had agreed to it.
"""
import pytest

from app.enums.order_status import (
    ORDER_STATUS_CODES,
    OrderStatus,
    can_transition,
)


def test_quote_can_only_be_approved_or_cancelled():
    assert can_transition("quote", "pending") is True
    assert can_transition("quote", "cancelled") is True

    # The one that must not be allowed.
    assert can_transition("quote", "delivered") is False
    assert can_transition("quote", "shipped") is False
    assert can_transition("quote", "processing") is False


def test_normal_flow_is_permitted():
    assert can_transition("pending", "processing") is True
    assert can_transition("processing", "shipped") is True
    assert can_transition("shipped", "delivered") is True


def test_pending_may_shortcut_to_delivered():
    """A counter sale is taken and handed over in one step."""
    assert can_transition("pending", "delivered") is True


def test_terminal_states_do_not_move():
    assert can_transition("delivered", "pending") is False
    assert can_transition("cancelled", "pending") is False


def test_no_op_transition_is_allowed():
    """Re-sending the current status must not error — clients retry."""
    assert can_transition("pending", "pending") is True
    assert can_transition("delivered", "delivered") is True


def test_unknown_or_missing_status_is_treated_as_pending():
    """Legacy rows predate the vocabulary and must not be frozen by it."""
    assert can_transition(None, "processing") is True
    assert can_transition("something-old", "delivered") is True
    assert can_transition(None, "quote") is False


def test_quote_sits_before_pending_in_the_code_map():
    assert ORDER_STATUS_CODES[OrderStatus.QUOTE.value] == 0
    assert ORDER_STATUS_CODES[OrderStatus.PENDING.value] == 1


def test_codes_are_unique():
    codes = list(ORDER_STATUS_CODES.values())
    assert len(codes) == len(set(codes))
