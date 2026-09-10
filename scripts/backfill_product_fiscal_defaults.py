"""Backfill: give existing products a unit of measure and an IVA row.

Why this exists
---------------
Products auto-created by an order import carry a name, a price and some codes
and nothing else — the spreadsheet has no fiscal columns. Two consequences, both
of which reach a legal document:

  1. **No `unit_measure`.** Hacienda requires `UnidadMedida` on every line, so
     billing anything built from such a product falls back to "Unid".
  2. **No taxes.** A line built from a product with no taxes carries no IVA, and
     an order costed against it totals to zero tax — which is exactly how 26
     existing orders came to report `taxes = 0`.

For a product created through the UI neither applies: the unit is a required
field now, and the IVA comes from the CABYS the operator picks. This fills in the
ones that predate that, and only those.

What it writes
--------------
* `unit_measure` — only when empty, and only to the default unit.
* a single IVA row — only when the product has NO taxes at all. The rate comes
  from the product's CABYS when it has one (that is what the taxonomy is for);
  otherwise the general 13%, which is the correct rate for a good or service
  with no exemption on record.

It never overwrites a tax the operator configured, and never touches a product
that already has one — a genuinely exempt article is expressed as a rate-10 row,
not as an absent one, so "no taxes" is unambiguously "never configured".

Usage
-----
    STAGE=dev AWS_PROFILE=<profile> AWS_REGION=us-east-1 \\
      python scripts/backfill_product_fiscal_defaults.py --dry-run
    ... --apply [--organization <org-id>] [--limit N]

Run `backfill_order_line_calculations.py` afterwards so existing orders pick the
new taxes up.
"""
from __future__ import annotations

import argparse
import logging
import sys

sys.path.insert(0, ".")

from app.enums.hacienda_codes import TaxRateCode, TaxType  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.repositories.product_repository import ProductRepository  # noqa: E402

logger = logging.getLogger("backfill-products")

#: Hacienda `UnidadMedida` for a discrete article — the right default for a
#: catalog entry, and the same one the POS form starts from.
DEFAULT_UNIT_MEASURE = "Unid"

#: General IVA rate. Used when the product has no CABYS to derive one from.
GENERAL_RATE_CODE = TaxRateCode.GENERAL_13.value
GENERAL_RATE_PERCENTAGE = 13.0


def _iva_row(product: Product) -> dict:
    """The IVA row this product should carry.

    Prefers the rate on the product's CABYS: that taxonomy exists precisely to
    say which rate applies, so a reduced or exempt article gets its real rate
    rather than the general one. Falls back to 13% when there is no CABYS —
    which is the case for every import-created product.
    """
    rate = product.cabys.tax_rate if product.cabys is not None else None

    percentage = (
        float(rate.percentage)
        if rate is not None and rate.percentage is not None
        else GENERAL_RATE_PERCENTAGE
    )
    code = (rate.code if rate is not None and rate.code else None) or GENERAL_RATE_CODE

    return {
        "tax_type_id": TaxType.IVA.value,
        "tax_rate": {
            # The CODE is what identifies the treatment; the percentage alone
            # does not (exento, no sujeto and crédito pleno are all 0%).
            "id": str(rate.id) if rate is not None and rate.id is not None else None,
            "percentage": percentage,
            "code": code,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="commit the changes")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--organization", help="limit to one organization id")
    parser.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with ProductRepository() as repo:
        query = repo.session.query(Product)
        if args.organization:
            query = query.filter(Product.organization_id == args.organization)
        query = query.order_by(Product.id)
        if args.limit:
            query = query.limit(args.limit)

        products = query.all()
        logger.info(
            "%s %d product(s)%s",
            "Backfilling" if args.apply else "Inspecting",
            len(products),
            "" if args.apply else " (dry run — nothing will be written)",
        )

        units_set = 0
        taxes_set = 0
        for product in products:
            changes = []

            if not (product.unit_measure or "").strip():
                product.unit_measure = DEFAULT_UNIT_MEASURE
                units_set += 1
                changes.append(f"unit={DEFAULT_UNIT_MEASURE}")

            if not product.taxes:
                row = _iva_row(product)
                product.taxes = [row]
                taxes_set += 1
                changes.append(
                    f"IVA {row['tax_rate']['percentage']}% (code {row['tax_rate']['code']})"
                )

            if changes:
                logger.info("  %-40s %s", (product.name or product.id)[:40], ", ".join(changes))

        logger.info(
            "%s: %d unit(s), %d tax row(s).",
            "Committed" if args.apply else "Would write",
            units_set,
            taxes_set,
        )
        if args.apply:
            repo.session.commit()
        else:
            repo.session.rollback()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
