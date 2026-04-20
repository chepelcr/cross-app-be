from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.session_request_dto import (
    SessionCreateRequestDTO,
    SessionUpdateRequestDTO,
)
from app.dtos.responses.session_dto import SessionResponse
from app.models.session import Session
from app.repositories.session_repository import SessionRepository

logger = logging.getLogger(__name__)


def get_sessions(
    organization_id: str,
    user_id: str,
    is_active: Optional[bool] = None,
    branch_id: Optional[str] = None,
    session_type: Optional[str] = None,
    context: Optional[str] = None,
) -> List[SessionResponse]:
    """Get all sessions for an organization with optional filters."""
    with SessionRepository() as repo:
        sessions = repo.find_all_by_organization(
            organization_id,
            is_active=is_active,
            branch_id=branch_id,
            session_type=session_type,
            context=context,
        )

    return [_map_session(s) for s in sessions]


def get_session(
    organization_id: str, user_id: str, session_id: str
) -> Optional[SessionResponse]:
    """Get a single session by ID."""
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
    if not session:
        return None
    return _map_session(session)


def create_session(
    organization_id: str,
    user_id: str,
    dto: SessionCreateRequestDTO,
) -> SessionResponse:
    """Create a new session."""
    with SessionRepository() as repo:
        # Validate branch exists if branch_id is provided
        if dto.branch_id:
            if not repo.validate_branch_exists(dto.branch_id, organization_id):
                raise ValueError(
                    f"Branch '{dto.branch_id}' does not exist or does not belong to this organization"
                )

        session_id = uuid.uuid4()

        session = Session(
            session_id=session_id,
            organization_id=organization_id,
            branch_id=uuid.UUID(dto.branch_id) if dto.branch_id else None,
            name=dto.name,
            type=dto.type,
            context=dto.context,
            start_time=dto.start_time,
            is_active=True,
            expected_revenue=dto.expected_revenue,
            created_by=user_id,
        )
        session = repo.save(session)

    return _map_session(session)


def update_session(
    organization_id: str,
    user_id: str,
    session_id: str,
    dto: SessionUpdateRequestDTO,
) -> Optional[SessionResponse]:
    """Update an existing session."""
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
        if not session:
            return None

        # Validate branch exists if branch_id is being updated
        if dto.branch_id is not None:
            if not repo.validate_branch_exists(dto.branch_id, organization_id):
                raise ValueError(
                    f"Branch '{dto.branch_id}' does not exist or does not belong to this organization"
                )

        # Update fields
        if dto.name is not None:
            session.name = dto.name
        if dto.type is not None:
            session.type = dto.type
        if dto.context is not None:
            session.context = dto.context
        if dto.branch_id is not None:
            session.branch_id = uuid.UUID(dto.branch_id)
        if dto.end_time is not None:
            session.end_time = dto.end_time
        if dto.expected_revenue is not None:
            session.expected_revenue = dto.expected_revenue
        if dto.actual_revenue is not None:
            session.actual_revenue = dto.actual_revenue

        # Handle session deactivation
        if dto.is_active is not None:
            session.is_active = dto.is_active
            # When deactivating, set end_time if not already set
            if not dto.is_active and session.end_time is None:
                session.end_time = datetime.now(timezone.utc)

        session = repo.save(session)

    return _map_session(session)


def delete_session(organization_id: str, user_id: str, session_id: str) -> bool:
    """Delete a session if it has no active assignments."""
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
        if not session:
            return False

        # Check for active assignments
        if repo.has_active_assignments(session_id):
            raise ValueError(
                "Cannot delete session with active assignments. "
                "Please end all active assignments first."
            )

        return repo.delete(session_id)


def _map_session(session: Session) -> SessionResponse:
    """Map Session model to SessionResponse DTO."""
    return SessionResponse(
        session_id=str(session.session_id),
        organization_id=session.organization_id,
        branch_id=str(session.branch_id) if session.branch_id else None,
        name=session.name,
        type=session.type,
        context=session.context,
        start_time=session.start_time.isoformat() if session.start_time else "",
        end_time=session.end_time.isoformat() if session.end_time else None,
        is_active=session.is_active,
        expected_revenue=float(session.expected_revenue) if session.expected_revenue else None,
        actual_revenue=float(session.actual_revenue) if session.actual_revenue else None,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        created_by=session.created_by,
    )
