"""Backfill: recompute existing orders' line amounts with the current engine.

Why this exists
---------------
Orders captured before the fiscal detail reached imported lines carry flat
numbers copied straight off the customer's spreadsheet: a `discount` that is
frequently zero even when the order header totals one, a `tax` nobody derived,
and no `taxes` / `discounts` / `cabys` / `net_price` at all. Such an order
cannot be billed without inventing a rate at invoice time.

This walks the existing rows and brings them up to what `order_service` now
produces on import:

  1. lines missing their fiscal detail get it from the linked product (CABYS,
     net price, the configured taxes, the unit of measure and the rest of the
     document line) and from the order (the discount, as **07 Descuento
     Comercial**);
  2. an order whose lines all show a zero discount while the HEADER totals one
     has that discount allocated across the lines in proportion to their gross —
     the same rule the import applies;
  3. every line is then recomputed through `LineCalculator`, and the order
     totals are re-added from the lines.

A line that ends up with no structured detail — no product, or a product with no
taxes configured — is left exactly as it was. Inventing a tax rate is worse than
carrying the customer's own figure.

Usage
-----
    STAGE=dev AWS_PROFILE=<profile> AWS_REGION=us-east-1 \\
      python scripts/backfill_order_line_calculations.py --dry-run
    STAGE=dev AWS_PROFILE=<profile> AWS_REGION=us-east-1 \\
      python scripts/backfill_order_line_calculations.py --apply

    # narrow it down while checking the result
    ... --apply --organization <org-id> --document <document-number> --limit 10

`--dry-run` is the default and prints the before/after totals per order without
writing anything. Nothing is committed unless `--apply` is passed.
"""
from __future__ import annotations

import argparse
import logging
import sys
from decimal import Decimal

sys.path.insert(0, ".")

from app.models.order import Order  # noqa: E402
from app.repositories.order_repository import OrderRepository  # noqa: E402
from app.repositories.product_repository import ProductRepository  # noqa: E402
from app.services.order_service import (  # noqa: E402
    _imported_line_discounts,
    _imported_line_net_price,
    _recompute_imported_line,
    _resum_order_totals,
    _imported_line_taxes,
)

logger = logging.getLogger("backfill")


def _allocate_over_lines(order: Order) -> dict[int, float]:
    """The header discount spread over lines that declare none.

    Mirrors `order_service._allocate_header_discount`, but reads an ORDER row
    rather than a freshly parsed spreadsheet — the original file is usually long
    gone by the time a backfill runs.
    """
    header = Decimal(str(order.discounts or 0))
    lines = list(order.lines or [])
    if header <= 0 or not lines:
        return {}
    if any(float(ln.discount or 0) > 0 for ln in lines):
        return {}

    gross = {
        ln.line_id: Decimal(str(ln.unit_price or 0))
        * Decimal(str(ln.quantity_ordered or ln.units_ordered or 0))
        for ln in lines
    }
    total = sum(gross.values())
    if total <= 0:
        return {}
    if header > total:
        header = total

    allocated = {
        key: (header * value / total).quantize(Decimal("0.00001"))
        for key, value in gross.items()
    }
    remainder = header - sum(allocated.values())
    if remainder:
        allocated[max(gross, key=lambda k: gross[k])] += remainder
    return {k: float(v) for k, v in allocated.items() if v > 0}


def _clear_bad_base_amounts(order: Order) -> None:
    """Undo a `base_amount` copied from the product by an earlier run.

    `OrderLine.base_amount` arrived with migration `bd0e1f2a3b4c` and is written
    from exactly two places: a manual order that carries one in its payload, and
    a briefly-shipped version of this script that wrongly copied the PRODUCT's
    computed base. Only the second kind exists on an imported order, so clearing
    it there restores the derived base without touching anything an operator set.
    """
    if (order.source or "").strip() == "manual":
        return
    for line in (order.lines or []):
        if line.base_amount is not None:
            line.base_amount = None


def backfill_order(order: Order, product_repo: ProductRepository) -> dict:
    """Bring one order's lines up to date. Returns a before/after summary."""
    before = {
        "discounts": float(order.discounts or 0),
        "taxes": float(order.taxes or 0),
        "grand_total": float(order.grand_total or 0),
    }

    _clear_bad_base_amounts(order)
    allocated = _allocate_over_lines(order)

    for line in (order.lines or []):
        product = line.product
        # Fill in whatever the line is missing; never overwrite what it has —
        # a hand-edited line's own detail is the user's, not ours to replace.
        if not line.cabys and product is not None and product.cabys:
            line.cabys = product.cabys.code
        if line.net_price is None:
            line.net_price = _imported_line_net_price(line, product)
        if not line.taxes and product is not None:
            line.taxes = _imported_line_taxes(product)

        # The rest of the document line (migration `bd0e1f2a3b4c`). These
        # columns are new, so every existing line has them empty — including
        # `unit_measure`, which Hacienda requires on every line and which the
        # invoice would otherwise have to guess as "Unid".
        #
        # `base_amount` is deliberately NOT among them. The product column of
        # that name is a computed OUTPUT (the IVA base at quantity 1), while the
        # line column is the editable-base OVERRIDE the calculator prices off —
        # copying one into the other pins a 23-unit line's tax to one unit's
        # base. It is set per line, by the operator, for tax code 07 or
        # IVACobradoFabrica 01, and nowhere else.
        if product is not None:
            if not line.unit_measure:
                line.unit_measure = product.unit_measure
            if not line.commercial_unit_measure:
                line.commercial_unit_measure = product.commercial_unit_measure
            if not line.customs_part:
                line.customs_part = product.customs_part
            if not line.iva_collected_factory:
                line.iva_collected_factory = product.iva_collected_factory
            if not line.codes and product.codes:
                # The product's array is the only source for a line imported
                # before the line carried its own codes. Newer imports write
                # the LINE's codes and this is skipped.
                line.codes = [dict(c) for c in product.codes]
        if not line.discounts:
            amount = float(line.discount or 0) or allocated.get(line.line_id, 0.0)
            if amount > 0:
                line.discount = amount
                line.discounts = _imported_line_discounts(amount)

        _recompute_imported_line(line, product)

    _resum_order_totals(order)

    after = {
        "discounts": float(order.discounts or 0),
        "taxes": float(order.taxes or 0),
        "grand_total": float(order.grand_total or 0),
    }
    return {"before": before, "after": after}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="commit the changes")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--organization", help="limit to one organization id")
    parser.add_argument("--document", help="limit to one document number")
    parser.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    apply_changes = args.apply

    with OrderRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)

        query = repo.session.query(Order)
        if args.organization:
            query = query.filter(Order.company_id == args.organization)
        if args.document:
            query = query.filter(Order.document_number == args.document)
        query = query.order_by(Order.order_id)
        if args.limit:
            query = query.limit(args.limit)

        orders = query.all()
        logger.info(
            "%s %d order(s)%s",
            "Backfilling" if apply_changes else "Inspecting",
            len(orders),
            "" if apply_changes else " (dry run — nothing will be written)",
        )

        changed = 0
        for order in orders:
            try:
                summary = backfill_order(order, product_repo)
            except Exception as exc:  # one bad order must not stop the run
                logger.warning("  %s: FAILED — %s", order.document_number, exc)
                continue

            moved = summary["before"] != summary["after"]
            if moved:
                changed += 1
            logger.info(
                "  %-16s total %12.2f -> %12.2f   tax %10.2f -> %10.2f%s",
                order.document_number,
                summary["before"]["grand_total"],
                summary["after"]["grand_total"],
                summary["before"]["taxes"],
                summary["after"]["taxes"],
                "" if moved else "   (unchanged)",
            )

        if apply_changes:
            repo.session.commit()
            logger.info("Committed. %d order(s) changed.", changed)
        else:
            repo.session.rollback()
            logger.info("Dry run complete. %d order(s) WOULD change.", changed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
