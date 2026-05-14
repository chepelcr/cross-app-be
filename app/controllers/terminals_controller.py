from __future__ import annotations

from typing import Annotated, Optional

from fastapi import FastAPI, Header, HTTPException, Path, Query

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
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals",
            response_model=TerminalListResponse,
            tags=["terminals"],
            summary="Get all terminals for a branch (by branch integer code)",
        )
        async def list_terminals(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(None),
            page: int = Query(1, ge=1),
            page_size: int = Query(12, ge=1, le=100),
        ) -> TerminalListResponse:
            try:
                return terminal_service.get_terminals(
                    organization_id, x_user_id, page=page, page_size=page_size,
                    search=search, branch_code=branch_code
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals/{terminal_code}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Get a specific terminal by its integer code within a branch",
        )
        async def get_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            terminal_code: Annotated[int, Path(description="Terminal integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                result = terminal_service.get_terminal_by_code(
                    organization_id, x_user_id, terminal_code, branch_code
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Terminal not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals",
            response_model=TerminalResponse,
            status_code=201,
            tags=["terminals"],
            summary="Create a new terminal under a branch",
            description="""Create a new terminal for a branch identified by its integer code.

**Required fields:**
- `name`: Terminal name
- `code`: Integer terminal code — must be unique within the organization (Hacienda requirement)

**Optional fields:**
- `device_id`: Physical device identifier (globally unique)
""",
        )
        async def create_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: TerminalCreateRequestDTO,
        ):
            try:
                return terminal_service.create_terminal(organization_id, x_user_id, body)
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals/{terminal_code}",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Update an existing terminal by its integer code",
        )
        async def update_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            terminal_code: Annotated[int, Path(description="Terminal integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: TerminalUpdateRequestDTO,
        ):
            try:
                result = terminal_service.update_terminal(
                    organization_id, x_user_id, terminal_code, branch_code, body
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
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals/{terminal_code}/status",
            response_model=TerminalResponse,
            tags=["terminals"],
            summary="Update terminal status",
            description="Update the status of a terminal (1=Active, 2=Inactive, 3=Deleted)",
        )
        async def update_terminal_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            terminal_code: Annotated[int, Path(description="Terminal integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: ProductStatusRequestDTO,
        ) -> TerminalResponse:
            try:
                result = terminal_service.update_terminal_status(
                    organization_id, x_user_id, terminal_code, branch_code, body.status
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
            "/api/organizations/{organization_id}/branches/{branch_code}/terminals/{terminal_code}",
            status_code=204,
            tags=["terminals"],
            summary="Delete a terminal by its integer code",
        )
        async def delete_terminal(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            terminal_code: Annotated[int, Path(description="Terminal integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                success = terminal_service.delete_terminal(
                    organization_id, x_user_id, terminal_code, branch_code
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
