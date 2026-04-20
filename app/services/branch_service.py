from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.branch_request_dto import (
    BranchCreateRequestDTO,
    BranchUpdateRequestDTO,
)
from app.dtos.responses.branch_dto import BranchResponse
from app.models.branch import Branch
from app.repositories.branch_repository import BranchRepository

logger = logging.getLogger(__name__)


def get_branches(
    organization_id: str,
    user_id: str,
    is_active: Optional[bool] = None,
    branch_type: Optional[str] = None,
) -> List[BranchResponse]:
    """Get all branches for an organization with optional filters."""
    with BranchRepository() as repo:
        branches = repo.find_all_by_organization(
            organization_id,
            is_active=is_active,
            branch_type=branch_type,
        )

    return [_map_branch(b) for b in branches]


def get_branch(
    organization_id: str, user_id: str, branch_id: str
) -> Optional[BranchResponse]:
    """Get a single branch by ID."""
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
        now = datetime.now(timezone.utc)

        branch = Branch(
            branch_id=branch_id,
            organization_id=organization_id,
            name=dto.name,
            code=dto.code,
            type=dto.type,
            is_active=True,
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
        if dto.is_active is not None:
            branch.is_active = dto.is_active
        if dto.address is not None:
            branch.address = dto.address
        if dto.phone is not None:
            branch.phone = dto.phone

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


def _map_branch(branch: Branch) -> BranchResponse:
    """Map Branch model to BranchResponse DTO."""
    return BranchResponse(
        branch_id=str(branch.branch_id),
        organization_id=branch.organization_id,
        name=branch.name,
        code=branch.code,
        type=branch.type,
        is_active=branch.is_active,
        address=branch.address,
        phone=branch.phone,
        created_at=branch.created_at.isoformat() if branch.created_at else "",
        updated_at=branch.updated_at.isoformat() if branch.updated_at else "",
        created_by=branch.created_by,
    )
