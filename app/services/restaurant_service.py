from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from app.dtos.requests.restaurant_request_dto import (
    ComboUpsertDTO,
    KitchenStationDTO,
    ModifierGroupCreateDTO,
    ModifierGroupUpdateDTO,
    ProductModifierGroupsDTO,
    ProductStationsDTO,
)
from app.dtos.responses.restaurant_dto import (
    ComboItemResponse,
    ComboResponse,
    KitchenStationListResponse,
    KitchenStationResponse,
    ModifierGroupListResponse,
    ModifierGroupResponse,
    ModifierResponse,
)
from app.models.restaurant import ComboItem, KitchenStation, Modifier, ModifierGroup
from app.repositories.branch_repository import BranchRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.restaurant_repository import RestaurantRepository

logger = logging.getLogger(__name__)


# ─── Combos ─────────────────────────────────────────────────────────────────

def get_combo(organization_id: str, combo_product_id: str) -> ComboResponse:
    with RestaurantRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)
        combo = product_repo.find_by_id_and_company(combo_product_id, organization_id)
        if not combo:
            raise LookupError(f"Product '{combo_product_id}' not found")

        items = repo.find_combo_items(combo_product_id)
        components = []
        for it in items:
            component = product_repo.find_by_id_and_company(it.product_id, organization_id)
            components.append(
                ComboItemResponse(
                    combo_item_id=str(it.combo_item_id),
                    product_id=it.product_id,
                    description=component.description if component else None,
                    # The POS needs each part's catalog price to work out the
                    # combo's discount without a second round trip.
                    unit_price=float(component.price) if component and component.price else None,
                    quantity=float(it.quantity or 1),
                    sort_order=it.sort_order or 0,
                )
            )

        return ComboResponse(
            combo_product_id=combo_product_id,
            price=float(combo.price) if combo.price else None,
            items=components,
        )


def upsert_combo(
    organization_id: str, combo_product_id: str, dto: ComboUpsertDTO
) -> ComboResponse:
    """Replace a combo's components.

    Marks the product `is_combo` as a side effect, so the flag and the component
    list can never disagree — a combo with no parts would explode into nothing.
    """
    with RestaurantRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)
        combo = product_repo.find_by_id_and_company(combo_product_id, organization_id)
        if not combo:
            raise LookupError(f"Product '{combo_product_id}' not found")

        rows: List[ComboItem] = []
        for idx, item in enumerate(dto.items):
            if item.product_id == combo_product_id:
                raise ValueError("A combo cannot contain itself")
            component = product_repo.find_by_id_and_company(item.product_id, organization_id)
            if not component:
                raise LookupError(f"Component product '{item.product_id}' not found")
            if getattr(component, "is_combo", False):
                # Nested combos would need recursive explosion and make the
                # discount distribution ambiguous.
                raise ValueError("A combo cannot contain another combo")
            rows.append(
                ComboItem(
                    combo_item_id=uuid.uuid4(),
                    combo_product_id=combo_product_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    sort_order=item.sort_order or idx,
                )
            )

        repo.replace_combo_items(combo_product_id, rows)
        combo.is_combo = True
        repo.session.flush()

    return get_combo(organization_id, combo_product_id)


# ─── Modifier groups ────────────────────────────────────────────────────────

def _map_group(group: ModifierGroup) -> ModifierGroupResponse:
    return ModifierGroupResponse(
        group_id=str(group.group_id),
        organization_id=group.organization_id,
        name=group.name,
        min_select=group.min_select or 0,
        max_select=group.max_select,
        required=bool(group.required),
        sort_order=group.sort_order or 0,
        modifiers=[
            ModifierResponse(
                modifier_id=str(m.modifier_id),
                name=m.name,
                price_delta=float(m.price_delta or 0),
                product_id=m.product_id,
                sort_order=m.sort_order or 0,
            )
            for m in sorted(group.modifiers or [], key=lambda x: x.sort_order or 0)
            if m.deleted_on is None
        ],
    )


def get_modifier_groups(organization_id: str) -> ModifierGroupListResponse:
    with RestaurantRepository() as repo:
        groups = repo.find_groups_by_organization(organization_id)
        return ModifierGroupListResponse(data=[_map_group(g) for g in groups])


def get_product_modifier_groups(product_id: str) -> ModifierGroupListResponse:
    with RestaurantRepository() as repo:
        groups = repo.find_groups_for_product(product_id)
        return ModifierGroupListResponse(data=[_map_group(g) for g in groups])


def create_modifier_group(
    organization_id: str, dto: ModifierGroupCreateDTO
) -> ModifierGroupResponse:
    with RestaurantRepository() as repo:
        group = ModifierGroup(
            group_id=uuid.uuid4(),
            organization_id=organization_id,
            name=dto.name,
            min_select=dto.min_select,
            max_select=dto.max_select,
            required=dto.required,
            sort_order=dto.sort_order,
        )
        for idx, m in enumerate(dto.modifiers):
            group.modifiers.append(
                Modifier(
                    modifier_id=uuid.uuid4(),
                    name=m.name,
                    price_delta=m.price_delta,
                    product_id=m.product_id,
                    sort_order=m.sort_order or idx,
                )
            )
        group = repo.save(group)
        return _map_group(group)


def update_modifier_group(
    organization_id: str, group_id: str, dto: ModifierGroupUpdateDTO
) -> ModifierGroupResponse:
    with RestaurantRepository() as repo:
        group = repo.find_group(uuid.UUID(group_id), organization_id)
        if not group:
            raise LookupError(f"Modifier group '{group_id}' not found")

        for field in ("name", "min_select", "max_select", "required", "sort_order"):
            value = getattr(dto, field)
            if value is not None:
                setattr(group, field, value)

        if dto.modifiers is not None:
            # Replace wholesale: a partial merge would need stable ids the
            # editor does not carry, and half-updated option lists are worse
            # than a rewrite.
            for existing in list(group.modifiers):
                repo.session.delete(existing)
            repo.session.flush()
            for idx, m in enumerate(dto.modifiers):
                group.modifiers.append(
                    Modifier(
                        modifier_id=uuid.uuid4(),
                        name=m.name,
                        price_delta=m.price_delta,
                        product_id=m.product_id,
                        sort_order=m.sort_order or idx,
                    )
                )

        group.updated_on = datetime.now(timezone.utc)
        group = repo.save(group)
        return _map_group(group)


def delete_modifier_group(organization_id: str, group_id: str) -> None:
    with RestaurantRepository() as repo:
        group = repo.find_group(uuid.UUID(group_id), organization_id)
        if not group:
            raise LookupError(f"Modifier group '{group_id}' not found")
        group.deleted_on = datetime.now(timezone.utc)
        group.status = 0
        repo.session.flush()


def set_product_modifier_groups(
    organization_id: str, product_id: str, dto: ProductModifierGroupsDTO
) -> ModifierGroupListResponse:
    with RestaurantRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)
        if not product_repo.find_by_id_and_company(product_id, organization_id):
            raise LookupError(f"Product '{product_id}' not found")

        ids = []
        for gid in dto.group_ids:
            group = repo.find_group(uuid.UUID(gid), organization_id)
            if not group:
                raise LookupError(f"Modifier group '{gid}' not found")
            ids.append(group.group_id)

        repo.set_product_groups(product_id, ids)

    return get_product_modifier_groups(product_id)


# ─── Kitchen stations ───────────────────────────────────────────────────────

def _map_station(station: KitchenStation) -> KitchenStationResponse:
    return KitchenStationResponse(
        station_id=str(station.station_id),
        organization_id=station.organization_id,
        branch_id=str(station.branch_id) if station.branch_id else None,
        name=station.name,
        printer_target=station.printer_target,
        sort_order=station.sort_order or 0,
    )


def get_kitchen_stations(organization_id: str) -> KitchenStationListResponse:
    with RestaurantRepository() as repo:
        return KitchenStationListResponse(
            data=[_map_station(s) for s in repo.find_stations(organization_id)]
        )


def create_kitchen_station(
    organization_id: str, dto: KitchenStationDTO
) -> KitchenStationResponse:
    with RestaurantRepository() as repo:
        branch_id = None
        if dto.branch_code is not None:
            branch_repo = BranchRepository.from_session(repo.session)
            branch = branch_repo.find_by_code_and_organization(dto.branch_code, organization_id)
            if not branch:
                raise LookupError(f"Branch '{dto.branch_code}' not found")
            branch_id = branch.branch_id

        station = KitchenStation(
            station_id=uuid.uuid4(),
            organization_id=organization_id,
            branch_id=branch_id,
            name=dto.name,
            printer_target=dto.printer_target,
            sort_order=dto.sort_order,
        )
        station = repo.save(station)
        return _map_station(station)


def set_product_stations(
    organization_id: str, product_id: str, dto: ProductStationsDTO
) -> None:
    """Route a product's comanda. An empty list means it does not print."""
    with RestaurantRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)
        if not product_repo.find_by_id_and_company(product_id, organization_id):
            raise LookupError(f"Product '{product_id}' not found")

        ids = []
        for sid in dto.station_ids:
            station = next(
                (s for s in repo.find_stations(organization_id) if str(s.station_id) == sid),
                None,
            )
            if not station:
                raise LookupError(f"Kitchen station '{sid}' not found")
            ids.append(station.station_id)

        repo.set_product_stations(product_id, ids)
