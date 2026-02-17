from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.client_request_dto import ClientRequestDTO
from app.dtos.requests.status_request_dto import StatusRequestDTO
from app.dtos.responses.client_dto import ClientListResponse, ClientResponse
from app.services import client_service


class ClientsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/clients",
            response_model=ClientListResponse,
            tags=["clients"],
            summary="Get all clients for an organization",
            description="""Get a paginated list of clients with optional search filters.

**Search filters**
- `clientName`: Client name (supports wildcards)
- `clientGln`: Client GLN code

**Sorting**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `clientName`, `clientGln`, `createdOn`, `updatedOn`

**Example:** `clientName:*corp*,orderBy>clientName`
""",
        )
        async def list_clients(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: clientName:*Test*,orderBy>clientName"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            try:
                return client_service.get_clients(
                    organization_id, page, pageSize, search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/clients/{client_id}",
            response_model=ClientResponse,
            tags=["clients"],
            summary="Get a specific client by ID",
        )
        async def get_client(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
        ):
            try:
                import uuid as uuid_mod

                result = client_service.get_client(uuid_mod.UUID(client_id))
                if not result:
                    raise HTTPException(status_code=404, detail="Client not found")
                return result
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid client ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/clients",
            response_model=ClientResponse,
            status_code=201,
            tags=["clients"],
            summary="Create a new client",
        )
        async def create_client(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: ClientRequestDTO,
        ):
            try:
                return client_service.create_client(organization_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.put(
            "/api/organizations/{organization_id}/clients/{client_id}",
            response_model=ClientResponse,
            tags=["clients"],
            summary="Update an existing client",
        )
        async def update_client(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            body: ClientRequestDTO,
        ):
            try:
                result = client_service.update_client(client_id, body)
                if not result:
                    raise HTTPException(status_code=404, detail="Client not found")
                return result
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid client ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/clients/{client_id}",
            response_model=ClientResponse,
            tags=["clients"],
            summary="Update client status",
        )
        async def update_client_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            client_id: Annotated[str, Path(description="Client UUID")],
            body: StatusRequestDTO = Body(...),
        ):
            try:
                result = client_service.update_client_status(client_id, body.status)
                if not result:
                    raise HTTPException(status_code=404, detail="Client not found")
                return result
            except HTTPException:
                raise
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid client ID format")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
