from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.dtos.requests.sale_point_request_dto import (
    SalePointCreateDTO,
    SalePointItemsDTO,
    SalePointUpdateDTO,
)
from app.dtos.responses.order_dto import OrderResponse
from app.mappers.orders_mapper import order_to_response
from app.models.crossdocking_item import CrossDockingItem
from app.models.crossdocking_sale_point import CrossDockingSalePoint
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository

logger = logging.getLogger(__name__)


def _load_order(repo: OrderRepository, organization_id: str, document_number: str):
    order = repo.find_by_company_and_document(organization_id, document_number)
    if not order:
        raise LookupError(f"Order '{document_number}' not found")
    return order


def _apply_items(
    repo: OrderRepository,
    order,
    sale_point: CrossDockingSalePoint,
    items: List,
    organization_id: str,
) -> None:
    """Replace a sale point's items and RE-DERIVE its totals.

    Totals are never taken from the caller: deriving them the same way the Excel
    parser does is what lets a hand-captured order reconcile against an imported
    one, and keeps the existing cross-docking report and PDF working unchanged.

    Allocating more than the order line ordered is rejected, naming the line —
    the check the spreadsheet path gets for free from its template.
    """
    product_repo = ProductRepository.from_session(repo.session)

    # What the order actually ordered, per product.
    ordered: dict[str, int] = {}
    for line in order.lines or []:
        if line.product_id:
            ordered[line.product_id] = (ordered.get(line.product_id, 0) or 0) + int(
                line.quantity_ordered or 0
            )

    # What other sale points on this order already claim.
    claimed: dict[str, int] = {}
    for sp in order.crossdocking_sale_points or []:
        if sp.sale_point_id == sale_point.sale_point_id:
            continue
        for it in sp.items or []:
            if it.product_id:
                claimed[it.product_id] = (claimed.get(it.product_id, 0) or 0) + int(
                    it.quantity or 0
                )

    for existing in list(sale_point.items or []):
        repo.session.delete(existing)
    repo.session.flush()

    total_boxes = 0
    total_units = 0

    for item in items:
        product = product_repo.find_by_id_and_company(item.product_id, organization_id)
        if not product:
            raise LookupError(f"Product '{item.product_id}' not found")

        available = ordered.get(item.product_id)
        if available is not None:
            over = claimed.get(item.product_id, 0) + item.quantity - available
            if over > 0:
                raise ValueError(
                    f"'{product.description or product.id}': allocating "
                    f"{claimed.get(item.product_id, 0) + item.quantity} of "
                    f"{available} ordered — {over} too many"
                )

        units_per_box = int(getattr(product, "units_per_box", 0) or 0) or 1
        units = item.quantity * units_per_box

        sale_point.items.append(
            CrossDockingItem(
                product_id=item.product_id,
                quantity=item.quantity,
                total_units=units,
                sent=0,
                missing=item.quantity,
            )
        )
        total_boxes += item.quantity
        total_units += units

    sale_point.total_boxes = total_boxes
    sale_point.total_units = total_units
    repo.session.flush()


def create_sale_point(
    organization_id: str, document_number: str, dto: SalePointCreateDTO
) -> OrderResponse:
    with OrderRepository() as repo:
        order = _load_order(repo, organization_id, document_number)

        name = dto.full_name
        store_id = None
        if dto.store_id:
            store_repo = StoreRepository.from_session(repo.session)
            store = store_repo.find_by_id_and_company(
                uuid.UUID(dto.store_id), organization_id
            )
            if not store:
                raise LookupError(f"Store '{dto.store_id}' not found")
            if order.client_id and store.client_id != order.client_id:
                raise ValueError("Delivery point does not belong to the order's client")
            store_id = store.store_id
            name = name or store.store_name or store.store_code

        if not name:
            raise ValueError("A sale point needs a registered store or a name")

        sale_point = CrossDockingSalePoint(
            order_id=order.order_id,
            store_id=store_id,
            full_name=name,
            total_boxes=0,
            total_units=0,
        )
        order.crossdocking_sale_points.append(sale_point)
        repo.session.flush()

        _apply_items(repo, order, sale_point, dto.items, organization_id)

        # Cross-docking is what order_type '73' means; a hand-captured
        # distribution is still cross-docking.
        if not order.order_type:
            order.order_type = "73"

        order = repo.save(order)
        return order_to_response(order)


def update_sale_point(
    organization_id: str, document_number: str, sale_point_id: int, dto: SalePointUpdateDTO
) -> OrderResponse:
    with OrderRepository() as repo:
        order = _load_order(repo, organization_id, document_number)
        sale_point = next(
            (sp for sp in order.crossdocking_sale_points or [] if sp.sale_point_id == sale_point_id),
            None,
        )
        if not sale_point:
            raise LookupError(f"Sale point '{sale_point_id}' not found on this order")

        if dto.full_name is not None:
            sale_point.full_name = dto.full_name

        order = repo.save(order)
        return order_to_response(order)


def set_sale_point_items(
    organization_id: str, document_number: str, sale_point_id: int, dto: SalePointItemsDTO
) -> OrderResponse:
    with OrderRepository() as repo:
        order = _load_order(repo, organization_id, document_number)
        sale_point = next(
            (sp for sp in order.crossdocking_sale_points or [] if sp.sale_point_id == sale_point_id),
            None,
        )
        if not sale_point:
            raise LookupError(f"Sale point '{sale_point_id}' not found on this order")

        _apply_items(repo, order, sale_point, dto.items, organization_id)
        order = repo.save(order)
        return order_to_response(order)


def delete_sale_point(
    organization_id: str, document_number: str, sale_point_id: int
) -> OrderResponse:
    with OrderRepository() as repo:
        order = _load_order(repo, organization_id, document_number)
        sale_point = next(
            (sp for sp in order.crossdocking_sale_points or [] if sp.sale_point_id == sale_point_id),
            None,
        )
        if not sale_point:
            raise LookupError(f"Sale point '{sale_point_id}' not found on this order")

        # Cascades to its items via the relationship.
        repo.session.delete(sale_point)
        repo.session.flush()

        order = repo.find_by_company_and_document(organization_id, document_number)
        return order_to_response(order)
