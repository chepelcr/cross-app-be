from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.closing_request_dto import (
    ClosingCreateRequestDTO,
    ClosingUpdateRequestDTO,
)
from app.dtos.requests.product_status_request_dto import ProductStatusRequestDTO
from app.dtos.responses.closing_dto import ClosingListResponse, ClosingResponse
from app.services import closing_service


class ClosingsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/closings",
            response_model=ClosingListResponse,
            tags=["closings"],
            summary="Get all closings for an organization",
            description="""Get a paginated list of closings with optional search filters.

**Query Parameters:**
- `search`: Search filter string (field:value syntax)
- `page`: Page number (1-indexed)
- `pageSize`: Items per page
- `session_id`: Filter by session UUID
- `status`: Filter by status ('pending', 'approved', 'rejected')
- `branch_id`: Filter by branch UUID

**Examples:**
- Get all closings: `/api/organizations/{orgId}/closings`
- Get pending closings: `/api/organizations/{orgId}/closings?status=pending`
- Get closings for a session: `/api/organizations/{orgId}/closings?session_id={sessionId}`
- Get closings for a branch: `/api/organizations/{orgId}/closings?branch_id={branchId}`
""",
        )
        async def list_closings(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: status:pending,orderBy>created_on"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
            session_id: Optional[str] = Query(
                None, description="Filter by session UUID"
            ),
            status: Optional[str] = Query(
                None, description="Filter by status (pending/approved/rejected)"
            ),
            branch_id: Optional[str] = Query(
                None, description="Filter by branch UUID"
            ),
        ) -> ClosingListResponse:
            try:
                return closing_service.get_closings(
                    organization_id, x_user_id, page=page, page_size=pageSize, search=search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/closings/{closing_id}",
            response_model=ClosingResponse,
            tags=["closings"],
            summary="Get a specific closing by ID",
        )
        async def get_closing(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            closing_id: Annotated[str, Path(description="Closing ID")],
        ):
            try:
                result = closing_service.get_closing(organization_id, x_user_id, closing_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Closing not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/closings",
            response_model=ClosingResponse,
            status_code=201,
            tags=["closings"],
            summary="Create a new closing",
            description="""Create a new cash register closing for an assignment.

**Required fields:**
- `session_id`: UUID of the session
- `assignment_id`: UUID of the assignment
- `declared_cash`: Declared cash amount from cashier
- `declared_sinpe`: Declared SINPE amount from cashier
- `declared_card`: Declared card amount from cashier
- `declared_total`: Declared total amount from cashier

**Optional fields:**
- `notes`: Optional notes from cashier

**Logic:**
1. Validates assignment exists and belongs to organization
2. Calculates expected amounts from orders associated with the assignment
3. Calculates differences between declared and expected amounts (done by database)
4. Creates closing record with status 'pending'

**Validation:**
- Assignment must exist and belong to the organization
- Only one closing per assignment is allowed
""",
        )
        async def create_closing(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: ClosingCreateRequestDTO,
        ):
            try:
                return closing_service.create_closing(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/closings/{closing_id}",
            response_model=ClosingResponse,
            tags=["closings"],
            summary="Update an existing closing",
            description="""Update a closing (typically for approval/rejection by managers).

**Updatable fields:**
- `status`: Closing status ('pending', 'approved', 'rejected')
- `reviewed_by`: User ID of the reviewer (manager) - automatically set if not provided
- `notes`: Optional notes

**Authorization:**
- Only managers can approve or reject closings (Requirement 5.7)
- Authorization enforcement should be done at API Gateway/auth layer
- Service layer provides defense-in-depth validation

**Logic:**
- When status is set to 'approved' or 'rejected', reviewed_by and reviewed_at are automatically set
- Attempting to approve/reject without manager role returns 403 Forbidden

**Error Responses:**
- 403: User does not have manager role for approval/rejection operations
- 404: Closing not found
- 400: Invalid request data
- 500: Internal server error
""",
        )
        async def update_closing(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            closing_id: Annotated[str, Path(description="Closing ID")],
            body: ClosingUpdateRequestDTO,
        ):
            try:
                # TODO: Get user role from API Gateway/auth layer via request context
                # For now, we assume all users are managers (is_manager=True)
                # In production, this should be extracted from JWT claims or auth context:
                # is_manager = request.state.user_role == 'manager'
                is_manager = True  # Placeholder - should be determined by auth layer

                result = closing_service.update_closing(
                    organization_id, x_user_id, closing_id, body, is_manager=is_manager
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Closing not found")
                return result
            except HTTPException:
                raise
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/closings/{closing_id}/status",
            response_model=ClosingResponse,
            tags=["closings"],
            summary="Update closing status",
            description="Update the status of a closing (1=pending, 2=approved, 3=rejected)",
        )
        async def update_closing_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            closing_id: Annotated[str, Path(description="Closing ID")],
            body: ProductStatusRequestDTO,
        ) -> ClosingResponse:
            try:
                result = closing_service.update_closing_status(
                    organization_id, x_user_id, closing_id, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Closing not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/closings/{closing_id}",
            status_code=204,
            tags=["closings"],
            summary="Delete a closing",
            description="""Delete a closing.

Returns 204 No Content on success.
""",
        )
        async def delete_closing(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            closing_id: Annotated[str, Path(description="Closing ID")],
        ):
            try:
                success = closing_service.delete_closing(
                    organization_id, x_user_id, closing_id
                )
                if not success:
                    raise HTTPException(status_code=404, detail="Closing not found")
                return None
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
