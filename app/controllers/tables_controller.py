from __future__ import annotations

from typing import Annotated

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.table_request_dto import (
    TableCreateRequestDTO,
    TableUpdateRequestDTO,
)
from app.dtos.responses.table_dto import TableListResponse, TableResponse
from app.services import table_service


class TablesController:
    """Mesas (restaurant) and cuentas abiertas (bar) — one resource.

    A tab is a dynamic table rather than a separate concept, so the bar vertical
    reuses these routes instead of adding its own.
    """

    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/branches/{branch_code}/tables",
            response_model=TableListResponse,
            tags=["tables"],
            summary="Mesas and open tabs for a branch",
            description="""Floor plan first, then open tabs — the order a cashier scans the room in.

Set `include_dynamic=false` to get only the fixed floor plan (e.g. when editing
the layout rather than serving).""",
        )
        async def list_tables(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Integer branch code, unique per org")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            include_dynamic: Annotated[bool, Query(description="Include open bar tabs")] = True,
        ) -> TableListResponse:
            try:
                return table_service.get_tables(
                    organization_id, branch_code, include_dynamic=include_dynamic
                )
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/branches/{branch_code}/tables",
            response_model=TableResponse,
            status_code=201,
            tags=["tables"],
            summary="Add a mesa, or open a bar tab",
            description="""Creates a table. `is_dynamic: true` opens a **bar tab** instead of adding
to the floor plan: the row is created on the fly, named after the customer, and
removed when the tab is paid.

Persisted server-side on purpose — a shift change or a device swap must not lose
an open tab. Codes are unique per branch.""",
        )
        async def create_table(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Integer branch code, unique per org")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: TableCreateRequestDTO = Body(...),
        ) -> TableResponse:
            try:
                return table_service.create_table(organization_id, branch_code, x_user_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/tables/{table_id}",
            response_model=TableResponse,
            tags=["tables"],
            summary="Update a table, or hold/release its order",
            description="""Send `held_document_id` to bind the active document tab to this table,
or `null` to release it. Everything else is presentation.""",
        )
        async def update_table(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            table_id: Annotated[str, Path(description="Table identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: TableUpdateRequestDTO = Body(...),
        ) -> TableResponse:
            try:
                return table_service.update_table(organization_id, table_id, body)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/tables/{table_id}",
            status_code=204,
            tags=["tables"],
            summary="Remove a mesa, or close a tab",
            description="""Soft delete — an order still points at the table it was taken at, and
breaking that link would break the receipt.

Returns **409** while the table still holds an open order: settle or move it
first, rather than silently orphaning the cart.""",
        )
        async def delete_table(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            table_id: Annotated[str, Path(description="Table identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ) -> None:
            try:
                table_service.delete_table(organization_id, table_id)
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
