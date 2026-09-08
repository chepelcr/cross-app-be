from __future__ import annotations

from typing import Annotated

from fastapi import Body, FastAPI, Header, HTTPException, Path

from app.dtos.requests.restaurant_request_dto import (
    ComboUpsertDTO,
    KitchenStationDTO,
    ModifierGroupCreateDTO,
    ModifierGroupUpdateDTO,
    ProductModifierGroupsDTO,
    ProductStationsDTO,
)
from app.dtos.responses.restaurant_dto import (
    ComboResponse,
    KitchenStationListResponse,
    KitchenStationResponse,
    ModifierGroupListResponse,
    ModifierGroupResponse,
)
from app.services import restaurant_service


class RestaurantController:
    """Combos, modifier groups and kitchen stations (TSR-154).

    Gated in the POS by the `restaurant` module, which the business type grants.
    """

    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):
        org = "/api/organizations/{organization_id}"

        # ── Combos ───────────────────────────────────────────────────────
        @app.get(
            f"{org}/products/{{product_id}}/combo",
            response_model=ComboResponse,
            tags=["restaurant"],
            summary="A combo's components and their catalog prices",
            description="""Returns the combo's own price plus each component with its catalog
unit price, which is what the POS needs to distribute the combo discount when
it explodes the line.

The combo price is **its own**, never the sum of the parts — that is the point
of a combo.""",
        )
        async def get_combo(
            organization_id: Annotated[str, Path()],
            product_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
        ) -> ComboResponse:
            try:
                return restaurant_service.get_combo(organization_id, product_id)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @app.put(
            f"{org}/products/{{product_id}}/combo",
            response_model=ComboResponse,
            tags=["restaurant"],
            summary="Replace a combo's components",
            description="""Sets the component list and marks the product as a combo, so the flag
and the parts can never disagree.

Rejects a combo containing **itself** or **another combo**: nested combos would
need recursive explosion and make the discount distribution ambiguous.""",
        )
        async def upsert_combo(
            organization_id: Annotated[str, Path()],
            product_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: ComboUpsertDTO = Body(...),
        ) -> ComboResponse:
            try:
                return restaurant_service.upsert_combo(organization_id, product_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        # ── Modifier groups ──────────────────────────────────────────────
        @app.get(
            f"{org}/modifier-groups",
            response_model=ModifierGroupListResponse,
            tags=["restaurant"],
            summary="The organization's modifier groups",
        )
        async def list_groups(
            organization_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
        ) -> ModifierGroupListResponse:
            return restaurant_service.get_modifier_groups(organization_id)

        @app.post(
            f"{org}/modifier-groups",
            response_model=ModifierGroupResponse,
            status_code=201,
            tags=["restaurant"],
            summary="Create a modifier group with its options",
            description="""A modifier with only a `price_delta` rides the parent line. One that
names a `product_id` becomes its **own** cart line, so its CABYS and IVA rate
are its own rather than inherited.""",
        )
        async def create_group(
            organization_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: ModifierGroupCreateDTO = Body(...),
        ) -> ModifierGroupResponse:
            try:
                return restaurant_service.create_modifier_group(organization_id, body)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @app.patch(
            f"{org}/modifier-groups/{{group_id}}",
            response_model=ModifierGroupResponse,
            tags=["restaurant"],
            summary="Update a group; sending `modifiers` replaces the whole list",
        )
        async def update_group(
            organization_id: Annotated[str, Path()],
            group_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: ModifierGroupUpdateDTO = Body(...),
        ) -> ModifierGroupResponse:
            try:
                return restaurant_service.update_modifier_group(organization_id, group_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @app.delete(
            f"{org}/modifier-groups/{{group_id}}",
            status_code=204,
            tags=["restaurant"],
            summary="Soft-delete a modifier group",
        )
        async def delete_group(
            organization_id: Annotated[str, Path()],
            group_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
        ) -> None:
            try:
                restaurant_service.delete_modifier_group(organization_id, group_id)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @app.get(
            f"{org}/products/{{product_id}}/modifier-groups",
            response_model=ModifierGroupListResponse,
            tags=["restaurant"],
            summary="Groups this product asks about, in order",
        )
        async def product_groups(
            organization_id: Annotated[str, Path()],
            product_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
        ) -> ModifierGroupListResponse:
            return restaurant_service.get_product_modifier_groups(product_id)

        @app.put(
            f"{org}/products/{{product_id}}/modifier-groups",
            response_model=ModifierGroupListResponse,
            tags=["restaurant"],
            summary="Set which groups a product asks about",
        )
        async def set_product_groups(
            organization_id: Annotated[str, Path()],
            product_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: ProductModifierGroupsDTO = Body(...),
        ) -> ModifierGroupListResponse:
            try:
                return restaurant_service.set_product_modifier_groups(
                    organization_id, product_id, body
                )
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        # ── Kitchen stations ─────────────────────────────────────────────
        @app.get(
            f"{org}/kitchen-stations",
            response_model=KitchenStationListResponse,
            tags=["restaurant"],
            summary="Kitchen/bar stations a comanda can print to",
        )
        async def list_stations(
            organization_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
        ) -> KitchenStationListResponse:
            return restaurant_service.get_kitchen_stations(organization_id)

        @app.post(
            f"{org}/kitchen-stations",
            response_model=KitchenStationResponse,
            status_code=201,
            tags=["restaurant"],
            summary="Create a kitchen station",
            description="""`printer_target` is a print destination NAME, not a driver — a browser
cannot address a thermal printer directly, so it maps to a destination the user
picks in the OS print dialog.""",
        )
        async def create_station(
            organization_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: KitchenStationDTO = Body(...),
        ) -> KitchenStationResponse:
            try:
                return restaurant_service.create_kitchen_station(organization_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @app.put(
            f"{org}/products/{{product_id}}/stations",
            status_code=204,
            tags=["restaurant"],
            summary="Route a product's comanda to stations (empty = does not print)",
        )
        async def set_stations(
            organization_id: Annotated[str, Path()],
            product_id: Annotated[str, Path()],
            x_user_id: Annotated[str, Header()],
            body: ProductStationsDTO = Body(...),
        ) -> None:
            try:
                restaurant_service.set_product_stations(organization_id, product_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
