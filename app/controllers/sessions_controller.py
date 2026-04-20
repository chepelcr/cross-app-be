from __future__ import annotations

from typing import Annotated, List, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.session_request_dto import (
    SessionCreateRequestDTO,
    SessionUpdateRequestDTO,
)
from app.dtos.responses.session_dto import SessionResponse
from app.services import session_service


class SessionsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/sessions",
            response_model=List[SessionResponse],
            tags=["sessions"],
            summary="Get all sessions for an organization",
            description="""Get a list of sessions with optional filters.

**Query Parameters:**
- `is_active`: Filter by active status (true/false)
- `branch_id`: Filter by branch UUID
- `type`: Filter by session type ('match' or 'shift')
- `context`: Filter by session context ('gradas', 'mesa', or 'caja')

**Examples:**
- Get all sessions: `/api/users/{userId}/organization/{orgId}/sessions`
- Get active sessions: `/api/users/{userId}/organization/{orgId}/sessions?is_active=true`
- Get match sessions: `/api/users/{userId}/organization/{orgId}/sessions?type=match`
- Get sessions for a branch: `/api/users/{userId}/organization/{orgId}/sessions?branch_id={branchId}`
""",
        )
        async def list_sessions(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            is_active: Optional[bool] = Query(
                None, description="Filter by active status"
            ),
            branch_id: Optional[str] = Query(
                None, description="Filter by branch UUID"
            ),
            type: Optional[str] = Query(
                None, description="Filter by session type (match/shift)"
            ),
            context: Optional[str] = Query(
                None, description="Filter by session context (gradas/mesa/caja)"
            ),
        ):
            try:
                return session_service.get_sessions(
                    organization_id,
                    user_id,
                    is_active=is_active,
                    branch_id=branch_id,
                    session_type=type,
                    context=context,
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/users/{user_id}/organization/{organization_id}/sessions/{session_id}",
            response_model=SessionResponse,
            tags=["sessions"],
            summary="Get a specific session by ID",
        )
        async def get_session(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            session_id: Annotated[str, Path(description="Session ID")],
        ):
            try:
                result = session_service.get_session(organization_id, user_id, session_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Session not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/users/{user_id}/organization/{organization_id}/sessions",
            response_model=SessionResponse,
            status_code=201,
            tags=["sessions"],
            summary="Create a new session",
            description="""Create a new session for an organization.

**Required fields:**
- `name`: Session name (e.g., "Partido vs Herediano", "Turno Mañana")
- `type`: Session type ('match' or 'shift')
- `context`: Session context ('gradas', 'mesa', or 'caja')
- `start_time`: Session start time (ISO timestamp)

**Optional fields:**
- `branch_id`: UUID of the branch for this session
- `expected_revenue`: Expected revenue for this session

**Validation:**
- If branch_id is provided, the branch must exist and belong to the organization
""",
        )
        async def create_session(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: SessionCreateRequestDTO,
        ):
            try:
                return session_service.create_session(organization_id, user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/users/{user_id}/organization/{organization_id}/sessions/{session_id}",
            response_model=SessionResponse,
            tags=["sessions"],
            summary="Update an existing session",
            description="""Update a session. Only provided fields are updated.

**Updatable fields:**
- `name`: Session name
- `type`: Session type ('match' or 'shift')
- `context`: Session context ('gradas', 'mesa', or 'caja')
- `branch_id`: UUID of the branch for this session
- `end_time`: Session end time (ISO timestamp)
- `is_active`: Active status (when set to false, end_time is automatically set if not provided)
- `expected_revenue`: Expected revenue
- `actual_revenue`: Actual revenue

**Validation:**
- If branch_id is provided, the branch must exist and belong to the organization
- When deactivating (is_active=false), end_time is automatically set to current time if not already set
""",
        )
        async def update_session(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            session_id: Annotated[str, Path(description="Session ID")],
            body: SessionUpdateRequestDTO,
        ):
            try:
                result = session_service.update_session(
                    organization_id, user_id, session_id, body
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Session not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/users/{user_id}/organization/{organization_id}/sessions/{session_id}",
            status_code=204,
            tags=["sessions"],
            summary="Delete a session",
            description="""Delete a session.

**Validation:**
- Cannot delete if session has active assignments

Returns 204 No Content on success.
""",
        )
        async def delete_session(
            user_id: Annotated[str, Path(description="User identifier")],
            organization_id: Annotated[str, Path(description="Organization identifier")],
            session_id: Annotated[str, Path(description="Session ID")],
        ):
            try:
                success = session_service.delete_session(
                    organization_id, user_id, session_id
                )
                if not success:
                    raise HTTPException(status_code=404, detail="Session not found")
                return None
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
