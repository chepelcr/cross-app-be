from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.assignment_request_dto import (
    AssignmentCreateRequestDTO,
    AssignmentUpdateRequestDTO,
)
from app.dtos.responses.assignment_dto import AssignmentResponse
from app.services import assignment_service


class AssignmentsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/assignments",
            response_model=List[AssignmentResponse],
            tags=["assignments"],
            summary="Get all assignments for an organization",
            description="""Get a list of assignments with optional filters.

**Query Parameters:**
- `is_active`: Filter by active status (true/false)
- `session_id`: Filter by session UUID
- `assigned_user_id`: Filter by assigned user ID
- `branch_id`: Filter by branch UUID

**Examples:**
- Get all assignments: `/api/users/{userId}/organization/{orgId}/assignments`
- Get active assignments: `/api/users/{userId}/organization/{orgId}/assignments?is_active=true`
- Get assignments for a session: `/api/users/{userId}/organization/{orgId}/assignments?session_id={sessionId}`
- Get assignments for a user: `/api/users/{userId}/organization/{orgId}/assignments?assigned_user_id={userId}`
""",
        )
        async def list_assignments(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            is_active: Optional[bool] = Query(
                None, description="Filter by active status"
            ),
            session_id: Optional[str] = Query(
                None, description="Filter by session UUID"
            ),
            assigned_user_id: Optional[str] = Query(
                None, description="Filter by assigned user ID"
            ),
            branch_id: Optional[str] = Query(
                None, description="Filter by branch UUID"
            ),
        ):
            try:
                return assignment_service.get_assignments(
                    organization_id,
                    user_id,
                    is_active=is_active,
                    session_id=session_id,
                    assigned_user_id=assigned_user_id,
                    branch_id=branch_id,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/assignments/{assignment_id}",
            response_model=AssignmentResponse,
            tags=["assignments"],
            summary="Get a specific assignment by ID",
        )
        async def get_assignment(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
        ):
            try:
                result = assignment_service.get_assignment(organization_id, user_id, assignment_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Assignment not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/users/{user_id}/organization/{organization_id}/assignments",
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
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: AssignmentCreateRequestDTO,
        ):
            try:
                return assignment_service.create_assignment(organization_id, user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/users/{user_id}/organization/{organization_id}/assignments/{assignment_id}",
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
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
            body: AssignmentUpdateRequestDTO,
        ):
            try:
                result = assignment_service.update_assignment(
                    organization_id, user_id, assignment_id, body
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

        @app.delete(
            "/api/users/{user_id}/organization/{organization_id}/assignments/{assignment_id}",
            status_code=204,
            tags=["assignments"],
            summary="Delete an assignment",
            description="""Delete an assignment.

Returns 204 No Content on success.
""",
        )
        async def delete_assignment(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            assignment_id: Annotated[str, Path(description="Assignment ID")],
        ):
            try:
                success = assignment_service.delete_assignment(
                    organization_id, user_id, assignment_id
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
