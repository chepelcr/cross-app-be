from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.product_status_request_dto import ProductStatusRequestDTO
from app.dtos.requests.terminal_request_dto import (
    TerminalCreateRequestDTO,
    TerminalUpdateRequestDTO,
)
from app.dtos.responses.terminal_dto import TerminalListResponse, TerminalResponse
from app.services import terminal_service


class TerminalsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals",
            response_model=TerminalListResponse,
            tags=["terminals"],
            summary="Get all terminals for a branch",
            description="""Get a paginated list of terminals for a specific branch.

**Query Parameters:**
- `search`: Search filter string (field:value syntax)
- `page`: Page number (1-indexed)
- `pageSize`: Items per page

**Examples:**
- Get all terminals for a branch: `/api/organizations/{orgId}/branches/{branchId}/terminals`
- Search by name: `/api/organizations/{orgId}/branches/{branchId}/terminals?search=name:*caja*`
""",
        )
        async def list_terminals(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: name:*caja*,orderBy>name"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
        ) -> TerminalListResponse:
            try:
                # Filter terminals by branch_id
                return terminal_service.get_terminals(
                    organization_id, x_user_id, page=page, page_size=pageSize, search=search, branch_id=branch_id
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals/{terminal_id}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Get a specific terminal by ID",
        )
        async def get_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
        ):
            try:
                result = terminal_service.get_terminal(organization_id, x_user_id, terminal_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                # Verify terminal belongs to the specified branch
                if result.get('branch_id') != branch_id:
                    raise HTTPException(status_code=404, detail="Terminal not found in this branch")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals",
            response_model=TerminalResponse,
            status_code=201,
            tags=["terminals"],
            summary="Create a new terminal",
            description="""Create a new terminal for a branch.

**Required fields:**
- `name`: Terminal name (e.g., "Terminal 1", "Caja Principal")
- `code`: Short code (e.g., "T1", "CP") - must be unique within organization

**Optional fields:**
- `device_id`: Physical device identifier (must be globally unique)

**Note:** The branch_id is taken from the URL path.
""",
        )
        async def create_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: TerminalCreateRequestDTO,
        ):
            try:
                # Override branch_id from URL path
                body.branch_id = branch_id
                return terminal_service.create_terminal(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals/{terminal_id}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Update an existing terminal",
            description="""Update a terminal. Only provided fields are updated.

**Updatable fields:**
- `name`: Terminal name
- `code`: Terminal code (must be unique within organization)
- `device_id`: Physical device identifier (must be globally unique)

**Note:** Cannot change branch_id through this endpoint.
""",
        )
        async def update_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
            body: TerminalUpdateRequestDTO,
        ):
            try:
                # Verify terminal belongs to the specified branch first
                existing = terminal_service.get_terminal(organization_id, x_user_id, terminal_id)
                if not existing:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                if existing.get('branch_id') != branch_id:
                    raise HTTPException(status_code=404, detail="Terminal not found in this branch")
                
                # Prevent changing branch_id through this endpoint
                if hasattr(body, 'branch_id') and body.branch_id is not None:
                    body.branch_id = None
                
                result = terminal_service.update_terminal(
                    organization_id, x_user_id, terminal_id, body
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals/{terminal_id}/status",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Update terminal status",
            description="Update the status of a terminal (1=Active, 2=Inactive, 3=Deleted)",
        )
        async def update_terminal_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
            body: ProductStatusRequestDTO,
        ) -> TerminalResponse:
            try:
                # Verify terminal belongs to the specified branch
                existing = terminal_service.get_terminal(organization_id, x_user_id, terminal_id)
                if not existing:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                if existing.get('branch_id') != branch_id:
                    raise HTTPException(status_code=404, detail="Terminal not found in this branch")
                
                result = terminal_service.update_terminal_status(
                    organization_id, x_user_id, terminal_id, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/branches/{branch_id}/terminals/{terminal_id}",
            status_code=204,
            tags=["terminals"],
            summary="Delete a terminal",
            description="""Delete a terminal.

**Validation:**
- Cannot delete if terminal has active assignments

Returns 204 No Content on success.
""",
        )
        async def delete_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
        ):
            try:
                # Verify terminal belongs to the specified branch
                existing = terminal_service.get_terminal(organization_id, x_user_id, terminal_id)
                if not existing:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                if existing.get('branch_id') != branch_id:
                    raise HTTPException(status_code=404, detail="Terminal not found in this branch")
                
                success = terminal_service.delete_terminal(
                    organization_id, x_user_id, terminal_id
                )
                if not success:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                return None
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
