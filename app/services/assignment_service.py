from __future__ import annotations

import logging
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.assignment_request_dto import (
    AssignmentCreateRequestDTO,
    AssignmentUpdateRequestDTO,
)
from app.dtos.responses.assignment_dto import AssignmentListResponse, AssignmentResponse, AssignmentUserDTO
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.assignment_search_filters import AssignmentSearchFilters
from app.models.assignment import Assignment
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.user_repository import UserRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_assignments(
    organization_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 12,
    search: Optional[str] = None,
) -> AssignmentListResponse:
    """Get all assignments for an organization with pagination and optional filters."""
    filters, order_by = (
        SearchUtils.parse_search_filter(search, Assignment, AssignmentSearchFilters)
        if search
        else ([], None)
    )

    with AssignmentRepository() as repo:
        assignments, total = repo.find_all_paginated(
            organization_id,
            filters=filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    # Batch-enrich with user data
    user_ids = list({a.user_id for a in assignments})
    users_map: Dict[str, object] = {}
    if user_ids:
        with UserRepository() as user_repo:
            users_map = user_repo.find_by_ids(user_ids)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return AssignmentListResponse(
        data=[_map_assignment(a, user=users_map.get(a.user_id)) for a in assignments],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total_elements=total,
            total_pages=total_pages,
        ),
    )


def get_assignment(
    organization_id: str, user_id: str, assignment_id: str
) -> Optional[AssignmentResponse]:
    """Get a single assignment by ID."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
    if not assignment:
        return None

    # Enrich with user data
    user = None
    with UserRepository() as user_repo:
        users_map = user_repo.find_by_ids([assignment.user_id])
        user = users_map.get(assignment.user_id)

    return _map_assignment(assignment, user=user)


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


def update_assignment_status(
    organization_id: str,
    user_id: str,
    assignment_id: str,
    status: int,
) -> Optional[AssignmentResponse]:
    """Update the status of an assignment. Status 3 (Deleted) sets deleted_on."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
        if not assignment:
            return None

        assignment.status = status
        if status != 1 and assignment.end_time is None:
            assignment.end_time = datetime.now(timezone.utc)
        if status == 3:
            assignment.deleted_on = datetime.now(timezone.utc)

        assignment = repo.save(assignment)

    return _map_assignment(assignment)


def delete_assignment(organization_id: str, user_id: str, assignment_id: str) -> bool:
    """Delete an assignment."""
    with AssignmentRepository() as repo:
        assignment = repo.find_by_id_and_organization(assignment_id, organization_id)
        if not assignment:
            return False

        return repo.delete(assignment_id)


def _map_assignment(assignment: Assignment, user=None) -> AssignmentResponse:
    """Map Assignment model to AssignmentResponse DTO."""
    # Derive status: prefer explicit status field if present, else derive from is_active
    try:
        status = int(assignment.status)
    except (AttributeError, TypeError):
        status = 1 if assignment.is_active else 2

    user_dto: Optional[AssignmentUserDTO] = None
    if user is not None:
        user_dto = AssignmentUserDTO(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )

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
        status=status,
        created_at=assignment.created_on.isoformat() if assignment.created_on else None,
        updated_at=assignment.updated_on.isoformat() if assignment.updated_on else None,
        created_by=assignment.created_by,
        user=user_dto,
    )
