from __future__ import annotations

from typing import Annotated, Optional

from fastapi import FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.branch_request_dto import (
    BranchCreateRequestDTO,
    BranchUpdateRequestDTO,
)
from app.dtos.requests.product_status_request_dto import ProductStatusRequestDTO
from app.dtos.responses.branch_dto import BranchListResponse, BranchResponse
from app.services import branch_service


class BranchesController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/branches",
            response_model=BranchListResponse,
            tags=["branches"],
            summary="Get all branches for an organization",
            description="""Get a paginated list of branches with optional search filters.

**Query Parameters:**
- `search`: Search filter string (field:value syntax)
- `page`: Page number (1-indexed)
- `page_size`: Items per page
- `type`: Filter by branch type ('stand' or 'restaurant')

**Examples:**
- Get all branches: `/api/organizations/{orgId}/branches`
- Get stands only: `/api/organizations/{orgId}/branches?type=stand`
""",
        )
        async def list_branches(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(None),
            page: int = Query(1, ge=1),
            page_size: int = Query(12, ge=1, le=100),
            type: Optional[str] = Query(None, description="Filter by branch type (stand/restaurant)"),
        ) -> BranchListResponse:
            try:
                return branch_service.get_branches(
                    organization_id, x_user_id, page=page, page_size=page_size, search=search, branch_type=type
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/branches/{branch_code}",
            response_model=BranchResponse,
            tags=["branches"],
            summary="Get a specific branch by its integer code",
        )
        async def get_branch(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code (unique per org)", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                result = branch_service.get_branch(organization_id, x_user_id, branch_code)
                if not result:
                    raise HTTPException(status_code=404, detail="Branch not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/branches",
            response_model=BranchResponse,
            status_code=201,
            tags=["branches"],
            summary="Create a new branch",
            description="""Create a new branch for an organization.

**Required fields:**
- `name`: Branch name
- `code`: Integer code (e.g. 1, 2) — must be unique within organization (Hacienda requirement)
- `type`: Branch type ('stand' or 'restaurant')
""",
        )
        async def create_branch(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: BranchCreateRequestDTO,
        ):
            try:
                return branch_service.create_branch(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/branches/{branch_code}",
            response_model=BranchResponse,
            tags=["branches"],
            summary="Update an existing branch by its integer code",
        )
        async def update_branch(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: BranchUpdateRequestDTO,
        ):
            try:
                result = branch_service.update_branch(
                    organization_id, x_user_id, branch_code, body
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Branch not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/branches/{branch_code}/status",
            response_model=BranchResponse,
            tags=["branches"],
            summary="Update branch status",
            description="Update the status of a branch (1=Active, 2=Inactive, 3=Deleted)",
        )
        async def update_branch_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: ProductStatusRequestDTO,
        ) -> BranchResponse:
            try:
                result = branch_service.update_branch_status(
                    organization_id, x_user_id, branch_code, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Branch not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/branches/{branch_code}",
            status_code=204,
            tags=["branches"],
            summary="Delete a branch by its integer code",
        )
        async def delete_branch(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_code: Annotated[int, Path(description="Branch integer code", ge=1)],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                success = branch_service.delete_branch(
                    organization_id, x_user_id, branch_code
                )
                if not success:
                    raise HTTPException(status_code=404, detail="Branch not found")
                return None
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
