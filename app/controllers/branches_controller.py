from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.branch_request_dto import (
    BranchCreateRequestDTO,
    BranchUpdateRequestDTO,
)
from app.dtos.responses.branch_dto import BranchResponse
from app.services import branch_service


class BranchesController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/branches",
            response_model=List[BranchResponse],
            tags=["branches"],
            summary="Get all branches for an organization",
            description="""Get a list of branches with optional filters.

**Query Parameters:**
- `is_active`: Filter by active status (true/false)
- `type`: Filter by branch type ('stand' or 'restaurant')

**Examples:**
- Get all branches: `/api/users/{userId}/organization/{orgId}/branches`
- Get active branches: `/api/users/{userId}/organization/{orgId}/branches?is_active=true`
- Get stands only: `/api/users/{userId}/organization/{orgId}/branches?type=stand`
""",
        )
        async def list_branches(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            is_active: Optional[bool] = Query(
                None, description="Filter by active status"
            ),
            type: Optional[str] = Query(
                None, description="Filter by branch type (stand/restaurant)"
            ),
        ):
            try:
                return branch_service.get_branches(
                    organization_id, user_id, is_active=is_active, branch_type=type
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/branches/{branch_id}",
            response_model=BranchResponse,
            tags=["branches"],
            summary="Get a specific branch by ID",
        )
        async def get_branch(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch ID")],
        ):
            try:
                result = branch_service.get_branch(organization_id, user_id, branch_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Branch not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/users/{user_id}/organization/{organization_id}/branches",
            response_model=BranchResponse,
            status_code=201,
            tags=["branches"],
            summary="Create a new branch",
            description="""Create a new branch for an organization.

**Required fields:**
- `name`: Branch name (e.g., "Puesto 1", "Restaurante Centro")
- `code`: Short code (e.g., "P1", "RC") - must be unique within organization
- `type`: Branch type ('stand' or 'restaurant')

**Optional fields:**
- `address`: Physical address
- `phone`: Contact phone number
""",
        )
        async def create_branch(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: BranchCreateRequestDTO,
        ):
            try:
                return branch_service.create_branch(organization_id, user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/users/{user_id}/organization/{organization_id}/branches/{branch_id}",
            response_model=BranchResponse,
            tags=["branches"],
            summary="Update an existing branch",
            description="""Update a branch. Only provided fields are updated.

**Updatable fields:**
- `name`: Branch name
- `code`: Branch code (must be unique within organization)
- `type`: Branch type ('stand' or 'restaurant')
- `is_active`: Active status
- `address`: Physical address
- `phone`: Contact phone number
""",
        )
        async def update_branch(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch ID")],
            body: BranchUpdateRequestDTO,
        ):
            try:
                result = branch_service.update_branch(
                    organization_id, user_id, branch_id, body
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

        @app.delete(
            "/api/users/{user_id}/organization/{organization_id}/branches/{branch_id}",
            status_code=204,
            tags=["branches"],
            summary="Delete a branch",
            description="""Delete a branch.

**Validation:**
- Cannot delete if branch has active terminals
- Cannot delete if branch has active sessions

Returns 204 No Content on success.
""",
        )
        async def delete_branch(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            branch_id: Annotated[str, Path(description="Branch ID")],
        ):
            try:
                success = branch_service.delete_branch(
                    organization_id, user_id, branch_id
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
