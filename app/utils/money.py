"""One definition of what a money amount is in the orders module.

**Order money is two decimals.** The colón has no sub-céntimo, the customer
spreadsheets these orders come from carry whole colones, and every surface that
shows an amount — the order PDF, the detail page, the ticket — formats it at two.
So that is what gets STORED, not a 5-decimal figure that only looks precise.

The columns are `NUMERIC(18,5)` and stay that way; the precision is a property of
the values we write, not of the column.

Why it matters beyond tidiness
------------------------------
A discount allocated across lines, a tax applied to each, and a total summed from
them will not reconcile unless the rounding happens at the LINE and the total is
summed from the rounded lines. Rounding only at the end produces an order whose
displayed lines do not add up to its displayed total — measured at ~47% of
randomly generated multi-line orders with a header discount, which is to say
routinely.

The rule, therefore:

    round each line -> sum the rounded lines -> that IS the total

`sum_money` exists so no call site is tempted to sum raw values and round after.

Not the same as document money
------------------------------
Hacienda's XSD allows five decimals and the biller
(`jbiller_common.hacienda.services.tax_service`) quantizes every `MontoImpuesto`
there. That is correct for a comprobante and is deliberately left alone: an order
is not a fiscal document, and the invoice built from one is recomputed by
sales-api at its own precision. These two roundings are separate on purpose.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

#: Two decimals — see the module docstring.
MONEY_QUANT = Decimal("0.01")


def to_decimal(value) -> Decimal:
    """Coerce anything money-shaped to `Decimal`, treating None as zero.

    Goes through `str` rather than `Decimal(float)` so 0.1 stays 0.1 instead of
    becoming 0.1000000000000000055511151231257827.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def q_money(value) -> Decimal:
    """Quantize to the stored precision, half-up. Returns a `Decimal`."""
    return to_decimal(value).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def round_money(value) -> float:
    """Quantize to the stored precision and return a float, for ORM assignment."""
    return float(q_money(value))


def sum_money(values: Iterable) -> Decimal:
    """Sum values that are ALREADY rounded, so the parts equal the whole.

    Use this for order totals. Summing unrounded line values and rounding the
    result gives a total the displayed lines do not add up to.
    """
    total = Decimal("0")
    for value in values:
        total += q_money(value)
    return total


def allocate_money(amount, weights: dict) -> dict:
    """Split `amount` across keys in proportion to `weights`, losing nothing.

    Each share is rounded to the stored precision, and the rounding remainder is
    given to the largest weight so the shares add back to `amount` exactly. A
    proportional split that does not do this leaves a céntimo unaccounted for,
    and on an order that céntimo is the difference between the lines and the
    header.

    Returns only the non-zero shares; an empty dict when there is nothing to
    split.
    """
    amount = q_money(amount)
    total_weight = sum(to_decimal(w) for w in weights.values())
    if amount <= 0 or total_weight <= 0:
        return {}

    shares = {
        key: q_money(amount * to_decimal(weight) / total_weight)
        for key, weight in weights.items()
    }
    remainder = amount - sum(shares.values())
    if remainder:
        largest = max(weights, key=lambda k: to_decimal(weights[k]))
        shares[largest] = q_money(shares[largest] + remainder)

    return {key: share for key, share in shares.items() if share > 0}
