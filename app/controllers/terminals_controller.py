from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.terminal_request_dto import (
    TerminalCreateRequestDTO,
    TerminalUpdateRequestDTO,
)
from app.dtos.responses.terminal_dto import TerminalResponse
from app.services import terminal_service


class TerminalsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/terminals",
            response_model=List[TerminalResponse],
            tags=["terminals"],
            summary="Get all terminals for an organization",
            description="""Get a list of terminals with optional filters.

**Query Parameters:**
- `is_active`: Filter by active status (true/false)
- `branch_id`: Filter by branch ID

**Examples:**
- Get all terminals: `/api/users/{userId}/organization/{orgId}/terminals`
- Get active terminals: `/api/users/{userId}/organization/{orgId}/terminals?is_active=true`
- Get terminals for a branch: `/api/users/{userId}/organization/{orgId}/terminals?branch_id={branchId}`
""",
        )
        async def list_terminals(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            is_active: Optional[bool] = Query(
                None, description="Filter by active status"
            ),
            branch_id: Optional[str] = Query(
                None, description="Filter by branch ID"
            ),
        ):
            try:
                return terminal_service.get_terminals(
                    organization_id, user_id, is_active=is_active, branch_id=branch_id
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/terminals/{terminal_id}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Get a specific terminal by ID",
        )
        async def get_terminal(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
        ):
            try:
                result = terminal_service.get_terminal(organization_id, user_id, terminal_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/users/{user_id}/organization/{organization_id}/terminals",
            response_model=TerminalResponse,
            status_code=201,
            tags=["terminals"],
            summary="Create a new terminal",
            description="""Create a new terminal for an organization.

**Required fields:**
- `branch_id`: UUID of the branch this terminal belongs to
- `name`: Terminal name (e.g., "Terminal 1", "Caja Principal")
- `code`: Short code (e.g., "T1", "CP") - must be unique within organization

**Optional fields:**
- `device_id`: Physical device identifier (must be globally unique)
""",
        )
        async def create_terminal(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: TerminalCreateRequestDTO,
        ):
            try:
                return terminal_service.create_terminal(organization_id, user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/users/{user_id}/organization/{organization_id}/terminals/{terminal_id}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Update an existing terminal",
            description="""Update a terminal. Only provided fields are updated.

**Updatable fields:**
- `name`: Terminal name
- `code`: Terminal code (must be unique within organization)
- `device_id`: Physical device identifier (must be globally unique)
- `is_active`: Active status
- `branch_id`: Branch assignment (must exist and belong to organization)
""",
        )
        async def update_terminal(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
            body: TerminalUpdateRequestDTO,
        ):
            try:
                result = terminal_service.update_terminal(
                    organization_id, user_id, terminal_id, body
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

        @app.delete(
            "/api/users/{user_id}/organization/{organization_id}/terminals/{terminal_id}",
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
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
        ):
            try:
                success = terminal_service.delete_terminal(
                    organization_id, user_id, terminal_id
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
