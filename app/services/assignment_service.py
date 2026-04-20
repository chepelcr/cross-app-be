from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.assignment_request_dto import (
    AssignmentCreateRequestDTO,
    AssignmentUpdateRequestDTO,
)
from app.dtos.responses.assignment_dto import AssignmentResponse
from app.models.assignment import Assignment
from app.repositories.assignment_repository import AssignmentRepository

logger = logging.getLogger(__name__)


def get_assignments(
    organization_id: str,
    user_id: str,
    is_active: Optional[bool] = None,
    session_id: Optional[str] = None,
    assigned_user_id: Optional[str] = None,
    branch_id: Optional[str] = None,
) -> List[AssignmentResponse]:
    """Get all assignments for an organization with optional filters."""
    with AssignmentRepository() as repo:
        assignments = repo.find_all_by_organization(
            organization_id,
            is_active=is_active,
            session_id=session_id,
            user_id=assigned_user_id,
            branch_id=branch_id,
        )

    return [_map_assignment(a) for a in assignments]


def get_assignment(
    organization_id: str, user_id: str, assignment_id: str
) -> Optional[AssignmentResponse]:
    """Get a single assignment by ID."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
    if not assignment:
        return None
    return _map_assignment(assignment)


def create_assignment(
    organization_id: str,
    user_id: str,
    dto: AssignmentCreateRequestDTO,
) -> AssignmentResponse:
    """Create a new assignment."""
    with AssignmentRepository() as repo:
        # Validate session exists, belongs to organization, and is active
        if not repo.validate_session_exists_and_active(dto.session_id, organization_id):
            raise ValueError(
                f"Session '{dto.session_id}' does not exist, does not belong to this organization, or is not active"
            )

        # Validate branch exists and belongs to organization
        if not repo.validate_branch_exists(dto.branch_id, organization_id):
            raise ValueError(
                f"Branch '{dto.branch_id}' does not exist or does not belong to this organization"
            )

        # Validate terminal exists and belongs to branch (if terminal_id provided)
        if dto.terminal_id:
            if not repo.validate_terminal_exists(dto.terminal_id, dto.branch_id):
                raise ValueError(
                    f"Terminal '{dto.terminal_id}' does not exist or does not belong to branch '{dto.branch_id}'"
                )

        # Check if user already has an active assignment
        # NOTE: We cannot validate if the user exists or is an org member because we don't have
        # access to the Markets API in this service. This is a known limitation.
        existing_assignment = repo.find_active_assignment_for_user(dto.user_id)
        if existing_assignment:
            raise ValueError(
                f"User '{dto.user_id}' already has an active assignment (assignment_id: {existing_assignment.assignment_id})"
            )

        assignment_id = uuid.uuid4()

        assignment = Assignment(
            assignment_id=assignment_id,
            organization_id=organization_id,
            session_id=uuid.UUID(dto.session_id),
            user_id=dto.user_id,
            branch_id=uuid.UUID(dto.branch_id),
            terminal_id=uuid.UUID(dto.terminal_id) if dto.terminal_id else None,
            role=dto.role,
            start_time=dto.start_time,
            is_active=True,
            created_by=user_id,
        )
        assignment = repo.save(assignment)

    return _map_assignment(assignment)


def update_assignment(
    organization_id: str,
    user_id: str,
    assignment_id: str,
    dto: AssignmentUpdateRequestDTO,
) -> Optional[AssignmentResponse]:
    """Update an existing assignment."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
        if not assignment:
            return None

        # Validate terminal exists and belongs to branch (if terminal_id is being updated)
        if dto.terminal_id is not None:
            if not repo.validate_terminal_exists(dto.terminal_id, str(assignment.branch_id)):
                raise ValueError(
                    f"Terminal '{dto.terminal_id}' does not exist or does not belong to branch '{assignment.branch_id}'"
                )

        # Update fields
        if dto.terminal_id is not None:
            assignment.terminal_id = uuid.UUID(dto.terminal_id)
        if dto.end_time is not None:
            assignment.end_time = dto.end_time

        # Handle assignment deactivation
        if dto.is_active is not None:
            assignment.is_active = dto.is_active
            # When deactivating, set end_time if not already set
            if not dto.is_active and assignment.end_time is None:
                assignment.end_time = datetime.now(timezone.utc)

        assignment = repo.save(assignment)

    return _map_assignment(assignment)


def delete_assignment(organization_id: str, user_id: str, assignment_id: str) -> bool:
    """Delete an assignment."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
        if not assignment:
            return False

        return repo.delete(assignment_id)


def _map_assignment(assignment: Assignment) -> AssignmentResponse:
    """Map Assignment model to AssignmentResponse DTO."""
    return AssignmentResponse(
        assignment_id=str(assignment.assignment_id),
        organization_id=assignment.organization_id,
        session_id=str(assignment.session_id),
        user_id=assignment.user_id,
        branch_id=str(assignment.branch_id),
        terminal_id=str(assignment.terminal_id) if assignment.terminal_id else None,
        role=assignment.role,
        start_time=assignment.start_time.isoformat() if assignment.start_time else "",
        end_time=assignment.end_time.isoformat() if assignment.end_time else None,
        is_active=assignment.is_active,
        created_at=assignment.created_at.isoformat() if assignment.created_at else "",
        updated_at=assignment.updated_at.isoformat() if assignment.updated_at else "",
        created_by=assignment.created_by,
    )
