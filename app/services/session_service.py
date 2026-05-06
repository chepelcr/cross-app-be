from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.session_request_dto import (
    SessionCreateRequestDTO,
    SessionUpdateRequestDTO,
)
from app.dtos.responses.pagination_dto import PaginationResponse
from app.dtos.responses.session_dto import SessionListResponse, SessionResponse
from app.enums.session_search_filters import SessionSearchFilters
from app.models.session import Session
from app.repositories.session_repository import SessionRepository
from app.repositories.session_product_repository import SessionProductRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_sessions(
    organization_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 12,
    search: Optional[str] = None,
) -> SessionListResponse:
    """Get all sessions for an organization with pagination and optional filters."""
    filters, order_by = (
        SearchUtils.parse_search_filter(search, Session, SessionSearchFilters)
        if search
        else ([], None)
    )

    with SessionRepository() as repo:
        sessions, total = repo.find_all_paginated(
            organization_id,
            filters=filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return SessionListResponse(
        data=[_map_session(s) for s in sessions],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total_elements=total,
            total_pages=total_pages,
        ),
    )


def get_session(
    organization_id: str, user_id: str, session_id: str
) -> Optional[SessionResponse]:
    """Get a single session by ID."""
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
    if not session:
        return None
    
    # Get product IDs for this session
    with SessionProductRepository() as sp_repo:
        session_products = sp_repo.find_by_session(session_id)
        product_ids = [sp.product_id for sp in session_products]
    
    return _map_session(session, product_ids)


def create_session(
    organization_id: str,
    user_id: str,
    dto: SessionCreateRequestDTO,
) -> SessionResponse:
    """Create a new session with optional assignments."""
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
            status=1,
            expected_revenue=dto.expected_revenue,
            created_by=user_id,
        )
        session = repo.save(session)

    # Save session products if provided
    product_ids = []
    if dto.product_ids:
        with SessionProductRepository() as sp_repo:
            sp_repo.bulk_create(
                session_id=str(session_id),
                organization_id=organization_id,
                product_ids=dto.product_ids,
            )
            product_ids = dto.product_ids

    # Create assignments if provided
    if dto.assignments:
        from app.repositories.assignment_repository import AssignmentRepository
        from app.models.assignment import Assignment
        
        with AssignmentRepository() as assign_repo:
            for assign_dto in dto.assignments:
                assignment = Assignment(
                    assignment_id=uuid.uuid4(),
                    organization_id=organization_id,
                    session_id=session_id,
                    user_id=uuid.UUID(assign_dto.user_id),
                    branch_id=uuid.UUID(assign_dto.branch_id),
                    terminal_id=uuid.UUID(assign_dto.terminal_id) if assign_dto.terminal_id else None,
                    role=assign_dto.role,
                    start_time=dto.start_time,
                    status=1,  # Active
                    created_by=user_id,
                )
                assign_repo.save(assignment)

    return _map_session(session, product_ids)


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

        session = repo.save(session)

    return _map_session(session)


def update_session_status(
    organization_id: str,
    user_id: str,
    session_id: str,
    status: int,
) -> Optional[SessionResponse]:
    """Update the status of a session.

    Status values: 1=Active, 2=Inactive, 3=Deleted.
    For any status other than 1, end_time is set to now if not already set.
    When deactivating or deleting, all active assignments are automatically ended.
    """
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
        if not session:
            return None

        # End all active assignments when deactivating or deleting session
        if status != 1:
            from app.repositories.assignment_repository import AssignmentRepository
            
            with AssignmentRepository() as assign_repo:
                # Find all active assignments for this session
                active_assignments = assign_repo.find_all_by_organization(
                    organization_id=organization_id,
                    session_id=session_id,
                    status=1  # Active
                )
                
                # End each assignment
                end_time = datetime.now(timezone.utc)
                for assignment in active_assignments:
                    assignment.end_time = end_time
                    assignment.status = 2  # Inactive
                    assign_repo.save(assignment)
                
                logger.info(
                    f"Ended {len(active_assignments)} active assignments for session {session_id}"
                )

        session.status = status
        if status != 1 and session.end_time is None:
            session.end_time = datetime.now(timezone.utc)
        if status == 3:
            session.deleted_on = datetime.now(timezone.utc)

        session = repo.save(session)

    return _map_session(session)


def delete_session(organization_id: str, user_id: str, session_id: str) -> bool:
    """Delete a session and automatically end all active assignments.
    
    This function will:
    1. End all active assignments for the session
    2. Delete the session
    
    Returns True if successful, False if session not found.
    """
    with SessionRepository() as repo:
        session = repo.find_by_id_and_organization(session_id, organization_id)
        if not session:
            return False

        # End all active assignments before deleting
        from app.repositories.assignment_repository import AssignmentRepository
        
        with AssignmentRepository() as assign_repo:
            # Find all active assignments for this session
            active_assignments = assign_repo.find_all_by_organization(
                organization_id=organization_id,
                session_id=session_id,
                status=1  # Active
            )
            
            # End each assignment
            end_time = datetime.now(timezone.utc)
            for assignment in active_assignments:
                assignment.end_time = end_time
                assignment.status = 2  # Inactive
                assign_repo.save(assignment)
            
            logger.info(
                f"Ended {len(active_assignments)} active assignments before deleting session {session_id}"
            )

        return repo.delete(session_id)


def _map_session(session: Session, product_ids: Optional[List[str]] = None) -> SessionResponse:
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
        status=session.status,
        expected_revenue=float(session.expected_revenue) if session.expected_revenue else None,
        actual_revenue=float(session.actual_revenue) if session.actual_revenue else None,
        created_at=session.created_on.isoformat() if session.created_on else None,
        updated_at=session.updated_on.isoformat() if session.updated_on else None,
        created_by=session.created_by,
        product_ids=product_ids,
    )
