from __future__ import annotations

import logging
from decimal import Decimal
from typing import List, Optional

from app.models.verticals import ProductUnit

logger = logging.getLogger(__name__)


class UnitConversionError(ValueError):
    """Raised when a unit is unknown or its factor is unusable."""


def base_unit(units: List[ProductUnit]) -> Optional[ProductUnit]:
    """The unit stock is counted in. Falls back to a factor of 1 when unmarked."""
    live = [u for u in units if u.deleted_on is None and u.status == 1]
    for unit in live:
        if unit.is_base:
            return unit
    for unit in live:
        if float(unit.factor_to_base or 0) == 1:
            return unit
    return None


def to_base_quantity(units: List[ProductUnit], unit_code: Optional[str], quantity: float) -> float:
    """Convert a sold quantity into BASE units for inventory.

    Sell 3 metros of a product stocked in rollos of 50 m and inventory moves by
    3, not by 3 rollos. Only the inventory side converts — the tax engine sees
    the sold quantity and its unit price, which is why this vertical never
    touches the Hacienda cascade.
    """
    if unit_code is None:
        return quantity

    unit = next(
        (u for u in units if u.unit_code == unit_code and u.deleted_on is None),
        None,
    )
    if unit is None:
        raise UnitConversionError(f"Unknown unit '{unit_code}' for this product")

    factor = Decimal(str(unit.factor_to_base or 0))
    if factor <= 0:
        # A zero or negative factor would silently zero out inventory movement.
        raise UnitConversionError(f"Unit '{unit_code}' has a non-positive conversion factor")

    return float(Decimal(str(quantity)) * factor)


def unit_price(
    units: List[ProductUnit], unit_code: Optional[str], base_price: float
) -> float:
    """Price for one of `unit_code`.

    An explicit `price_override` wins — a shop rarely wants "price per metro"
    to be exactly 1/50th of the rollo price, and rounding it would lose money on
    every cut. Without an override the base price is scaled by the factor.
    """
    if unit_code is None:
        return base_price

    unit = next(
        (u for u in units if u.unit_code == unit_code and u.deleted_on is None),
        None,
    )
    if unit is None:
        raise UnitConversionError(f"Unknown unit '{unit_code}' for this product")

    if unit.price_override is not None:
        return float(unit.price_override)

    factor = Decimal(str(unit.factor_to_base or 1))
    return float(Decimal(str(base_price)) * factor)
