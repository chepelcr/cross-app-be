"""Correct an order's status, including backwards.

`ORDER_STATUS_TRANSITIONS` is deliberately forward-only: `shipped` cannot go
back to `processing` through the API, because in the normal course of business
an order that has shipped has shipped. That is the right rule for the workflow
and the wrong one for a mis-click, which is what this script is for.

It is a correction tool, not a workflow bypass:

  * it names the order, prints its current status, and requires `--apply`;
  * it refuses a status that is not in the vocabulary;
  * it logs the before and after so the change is traceable.

Usage
-----
    STAGE=dev AWS_PROFILE=<profile> AWS_REGION=us-east-1 \\
      python scripts/set_order_status.py --document 2900679405 --status processing
    ... --document 2900679405 --status processing --apply

`--organization` narrows the search when the same document number exists for
more than one organization; without it the script refuses to guess.
"""
from __future__ import annotations

import argparse
import logging
import sys

sys.path.insert(0, ".")

from app.enums.order_status import ORDER_STATUS_CODES  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.repositories.order_repository import OrderRepository  # noqa: E402

logger = logging.getLogger("set-order-status")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--document", required=True, help="order document number")
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(ORDER_STATUS_CODES),
        help="target status",
    )
    parser.add_argument("--organization", help="organization id, when ambiguous")
    parser.add_argument("--apply", action="store_true", help="commit the change")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with OrderRepository() as repo:
        query = repo.session.query(Order).filter(Order.document_number == args.document)
        if args.organization:
            query = query.filter(Order.company_id == args.organization)
        orders = query.all()

        if not orders:
            logger.error("No order %s found.", args.document)
            return 1
        if len(orders) > 1:
            logger.error(
                "Order %s exists for %d organizations — pass --organization:\n%s",
                args.document,
                len(orders),
                "\n".join(f"  {o.company_id}" for o in orders),
            )
            return 1

        order = orders[0]
        logger.info(
            "Order %s (org %s): %s -> %s",
            order.document_number,
            order.company_id,
            order.order_status,
            args.status,
        )

        if order.order_status == args.status:
            logger.info("Already in that status; nothing to do.")
            repo.session.rollback()
            return 0

        if not args.apply:
            logger.info("Dry run — pass --apply to commit.")
            repo.session.rollback()
            return 0

        order.order_status = args.status
        repo.session.commit()
        logger.info("Committed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
