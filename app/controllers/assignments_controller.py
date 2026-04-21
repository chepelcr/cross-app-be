from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.assignment_request_dto import (
    AssignmentCreateRequestDTO,
    AssignmentUpdateRequestDTO,
)
from app.dtos.requests.product_status_request_dto import ProductStatusRequestDTO
from app.dtos.responses.assignment_dto import AssignmentListResponse, AssignmentResponse
from app.services import assignment_service


class AssignmentsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/assignments",
            response_model=AssignmentListResponse,
            tags=["assignments"],
            summary="Get all assignments for an organization",
            description="""Get a paginated list of assignments with optional search filters.

**Query Parameters:**
- `search`: Search filter string (field:value syntax)
- `page`: Page number (1-indexed)
- `pageSize`: Items per page
- `session_id`: Filter by session UUID
- `assigned_user_id`: Filter by assigned user ID
- `branch_id`: Filter by branch UUID

**Examples:**
- Get all assignments: `/api/organizations/{orgId}/assignments`
- Get assignments for a session: `/api/organizations/{orgId}/assignments?session_id={sessionId}`
- Get assignments for a user: `/api/organizations/{orgId}/assignments?assigned_user_id={userId}`
""",
        )
        async def list_assignments(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: role:cashier,orderBy>start_time"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
            session_id: Optional[str] = Query(
                None, description="Filter by session UUID"
            ),
            assigned_user_id: Optional[str] = Query(
                None, description="Filter by assigned user ID"
            ),
            branch_id: Optional[str] = Query(
                None, description="Filter by branch UUID"
            ),
        ) -> AssignmentListResponse:
            try:
                return assignment_service.get_assignments(
                    organization_id, x_user_id, page=page, page_size=pageSize, search=search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/assignments/{assignment_id}",
            response_model=AssignmentResponse,
            tags=["assignments"],
            summary="Get a specific assignment by ID",
        )
        async def get_assignment(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                result = assignment_service.get_assignment(organization_id, x_user_id, assignment_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/assignments",
            response_model=AssignmentResponse,
            status_code=201,
            tags=["assignments"],
            summary="Create a new assignment",
            description="""Create a new assignment for a cashier/supervisor.

**Required fields:**
- `session_id`: UUID of the session (must be active)
- `user_id`: User ID of the cashier/supervisor
- `branch_id`: UUID of the branch
- `role`: Role ('cashier' or 'supervisor')
- `start_time`: Assignment start time (ISO timestamp)

**Optional fields:**
- `terminal_id`: UUID of the terminal (if assigned to a specific terminal)

**Validation:**
- Session must exist, belong to the organization, and be active
- Branch must exist and belong to the organization
- Terminal must exist and belong to the branch (if terminal_id provided)
- User cannot have another active assignment
- NOTE: User existence and org membership validation is not performed (limitation: no access to Markets API)
""",
        )
        async def create_assignment(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: AssignmentCreateRequestDTO,
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                return assignment_service.create_assignment(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/assignments/{assignment_id}",
            response_model=AssignmentResponse,
            tags=["assignments"],
            summary="Update an existing assignment",
            description="""Update an assignment. Only provided fields are updated.

**Updatable fields:**
- `terminal_id`: UUID of the terminal
- `end_time`: Assignment end time (ISO timestamp)
- `is_active`: Active status (when set to false, end_time is automatically set if not provided)

**Validation:**
- Terminal must exist and belong to the branch (if terminal_id provided)
- When deactivating (is_active=false), end_time is automatically set to current time if not already set
""",
        )
        async def update_assignment(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
            body: AssignmentUpdateRequestDTO,
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                result = assignment_service.update_assignment(
                    organization_id, x_user_id, assignment_id, body
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/assignments/{assignment_id}/status",
            response_model=AssignmentResponse,
            tags=["assignments"],
            summary="Update assignment status",
            description="Update the status of an assignment (1=Active, 2=Inactive, 3=Deleted)",
        )
        async def update_assignment_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
            body: ProductStatusRequestDTO,
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ) -> AssignmentResponse:
            try:
                result = assignment_service.update_assignment_status(
                    organization_id, x_user_id, assignment_id, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/assignments/{assignment_id}",
            status_code=204,
            tags=["assignments"],
            summary="Delete an assignment",
            description="""Delete an assignment.

Returns 204 No Content on success.
""",
        )
        async def delete_assignment(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ):
            try:
                success = assignment_service.delete_assignment(
                    organization_id, x_user_id, assignment_id
                )
                if not success:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return None
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
