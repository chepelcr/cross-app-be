from __future__ import annotations

import logging
from typing import Dict, List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.branch_request_dto import (
    BranchCreateRequestDTO,
    BranchUpdateRequestDTO,
)
from app.dtos.responses.branch_dto import BranchListResponse, BranchResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.dtos.responses.terminal_dto import TerminalResponse
from app.enums.branch_search_filters import BranchSearchFilters
from app.models.branch import Branch
from app.repositories.branch_repository import BranchRepository
from app.repositories.terminal_repository import TerminalRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_branches(
    organization_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 12,
    search: Optional[str] = None,
    branch_type: Optional[str] = None,
) -> BranchListResponse:
    """Get all branches for an organization with pagination and optional filters."""
    filters, order_by = (
        SearchUtils.parse_search_filter(search, Branch, BranchSearchFilters)
        if search
        else ([], None)
    )

    # Apply branch_type filter outside of search string if provided
    if branch_type is not None:
        from sqlalchemy import and_
        from app.models.branch import Branch as BranchModel
        filters = list(filters)
        filters.append(BranchModel.type == branch_type)

    with BranchRepository() as repo:
        branches, total = repo.find_all_paginated(
            organization_id,
            filters=filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    # Batch-load terminals for all branches
    branch_ids = [str(b.branch_id) for b in branches]
    terminals_map: Dict[str, List] = {}
    if branch_ids:
        with TerminalRepository() as t_repo:
            terminals_map = t_repo.find_all_by_branch_ids(branch_ids)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return BranchListResponse(
        data=[_map_branch(b, terminals_map=terminals_map) for b in branches],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_branch(
    organization_id: str, user_id: str, branch_id: str
) -> Optional[BranchResponse]:
    """Get a single branch by ID, embedding its terminals."""
    with BranchRepository() as repo:
        branch = repo.find_by_id_and_organization(branch_id, organization_id)
    if not branch:
        return None
    return _map_branch(branch)


def create_branch(
    organization_id: str,
    user_id: str,
    dto: BranchCreateRequestDTO,
) -> BranchResponse:
    """Create a new branch."""
    with BranchRepository() as repo:
        # Check code uniqueness within organization
        existing = repo.find_by_code_and_organization(dto.code, organization_id)
        if existing:
            raise ValueError(
                f"Branch code '{dto.code}' already exists in this organization"
            )

        branch_id = uuid.uuid4()

        branch = Branch(
            branch_id=branch_id,
            organization_id=organization_id,
            name=dto.name,
            code=dto.code,
            type=dto.type,
            address=dto.address,
            phone=dto.phone,
            created_by=user_id,
        )
        branch = repo.save(branch)

    return _map_branch(branch)


def update_branch(
    organization_id: str,
    user_id: str,
    branch_id: str,
    dto: BranchUpdateRequestDTO,
) -> Optional[BranchResponse]:
    """Update an existing branch."""
    with BranchRepository() as repo:
        branch = repo.find_by_id_and_organization(branch_id, organization_id)
        if not branch:
            return None

        # Check code uniqueness if updating code
        if dto.code and dto.code != branch.code:
            existing = repo.find_by_code_and_organization(dto.code, organization_id)
            if existing:
                raise ValueError(
                    f"Branch code '{dto.code}' already exists in this organization"
                )

        # Update fields
        if dto.name is not None:
            branch.name = dto.name
        if dto.code is not None:
            branch.code = dto.code
        if dto.type is not None:
            branch.type = dto.type
        if dto.address is not None:
            branch.address = dto.address
        if dto.phone is not None:
            branch.phone = dto.phone

        branch = repo.save(branch)

    return _map_branch(branch)


def update_branch_status(
    organization_id: str,
    user_id: str,
    branch_id: str,
    status: int,
) -> Optional[BranchResponse]:
    """Update the status of a branch. Status 3 (Deleted) sets deleted_on."""
    with BranchRepository() as repo:
        branch = repo.find_by_id_and_organization(branch_id, organization_id)
        if not branch:
            return None

        branch.status = status
        if status == 3:
            branch.deleted_on = datetime.now(timezone.utc)

        branch = repo.save(branch)

    return _map_branch(branch)


def delete_branch(organization_id: str, user_id: str, branch_id: str) -> bool:
    """Delete a branch if it has no active terminals or sessions."""
    with BranchRepository() as repo:
        branch = repo.find_by_id_and_organization(branch_id, organization_id)
        if not branch:
            return False

        # Check for active terminals
        if repo.has_active_terminals(branch_id):
            raise ValueError(
                "Cannot delete branch with active terminals. "
                "Please deactivate or delete terminals first."
            )

        # Check for active sessions
        if repo.has_active_sessions(branch_id):
            raise ValueError(
                "Cannot delete branch with active sessions. "
                "Please end all active sessions first."
            )

        return repo.delete(branch_id)


def _map_branch(
    branch: Branch,
    terminals_map: Optional[Dict[str, list]] = None,
) -> BranchResponse:
    """Map Branch model to BranchResponse DTO."""
    # Load terminals for single-branch fetch (no terminals_map provided)
    if terminals_map is not None:
        raw_terminals = terminals_map.get(str(branch.branch_id), [])
    else:
        with TerminalRepository() as t_repo:
            raw_terminals = t_repo.find_all_by_branch(str(branch.branch_id))

    terminals = [_map_terminal_embed(t) for t in raw_terminals]

    return BranchResponse(
        branch_id=str(branch.branch_id),
        organization_id=branch.organization_id,
        name=branch.name,
        code=branch.code,
        type=branch.type,
        status=branch.status,
        address=branch.address,
        phone=branch.phone,
        created_at=branch.created_on.isoformat() if branch.created_on else None,
        updated_at=branch.updated_on.isoformat() if branch.updated_on else None,
        created_by=branch.created_by,
        terminals=terminals,
    )


def _map_terminal_embed(terminal) -> TerminalResponse:
    """Map Terminal model to TerminalResponse DTO (used when embedding in branches)."""
    return TerminalResponse(
        terminal_id=str(terminal.terminal_id),
        organization_id=terminal.organization_id,
        branch_id=str(terminal.branch_id),
        name=terminal.name,
        code=terminal.code,
        device_id=terminal.device_id,
        status=terminal.status,
        registered_at=terminal.registered_at.isoformat() if terminal.registered_at else None,
        last_seen_at=terminal.last_seen_at.isoformat() if terminal.last_seen_at else None,
        created_at=terminal.created_on.isoformat() if terminal.created_on else None,
        updated_at=terminal.updated_on.isoformat() if terminal.updated_on else None,
    )
