from __future__ import annotations

import logging
from typing import List, Optional
import uuid
from datetime import datetime, timezone

from app.dtos.requests.terminal_request_dto import (
    TerminalCreateRequestDTO,
    TerminalUpdateRequestDTO,
)
from app.dtos.responses.terminal_dto import TerminalResponse
from app.models.terminal import Terminal
from app.repositories.terminal_repository import TerminalRepository

logger = logging.getLogger(__name__)


def get_terminals(
    organization_id: str,
    user_id: str,
    is_active: Optional[bool] = None,
    branch_id: Optional[str] = None,
) -> List[TerminalResponse]:
    """Get all terminals for an organization with optional filters."""
    with TerminalRepository() as repo:
        terminals = repo.find_all_by_organization(
            organization_id,
            is_active=is_active,
            branch_id=branch_id,
        )

    return [_map_terminal(t) for t in terminals]


def get_terminal(
    organization_id: str, user_id: str, terminal_id: str
) -> Optional[TerminalResponse]:
    """Get a single terminal by ID."""
    with TerminalRepository() as repo:
        terminal = repo.find_by_id_and_organization(terminal_id, organization_id)
    if not terminal:
        return None
    return _map_terminal(terminal)


def create_terminal(
    organization_id: str,
    user_id: str,
    dto: TerminalCreateRequestDTO,
) -> TerminalResponse:
    """Create a new terminal."""
    with TerminalRepository() as repo:
        # Validate branch exists and belongs to organization
        if not repo.validate_branch_exists(dto.branch_id, organization_id):
            raise ValueError(
                f"Branch '{dto.branch_id}' does not exist or does not belong to this organization"
            )

        # Check code uniqueness within organization
        existing = repo.find_by_code_and_organization(dto.code, organization_id)
        if existing:
            raise ValueError(
                f"Terminal code '{dto.code}' already exists in this organization"
            )

        # Check device_id uniqueness globally (if provided)
        if dto.device_id:
            existing_device = repo.find_by_device_id(dto.device_id)
            if existing_device:
                raise ValueError(
                    f"Device ID '{dto.device_id}' is already registered to another terminal"
                )

        terminal_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        terminal = Terminal(
            terminal_id=terminal_id,
            organization_id=organization_id,
            branch_id=uuid.UUID(dto.branch_id),
            name=dto.name,
            code=dto.code,
            device_id=dto.device_id,
            is_active=True,
            registered_at=now,
        )
        terminal = repo.save(terminal)

    return _map_terminal(terminal)


def update_terminal(
    organization_id: str,
    user_id: str,
    terminal_id: str,
    dto: TerminalUpdateRequestDTO,
) -> Optional[TerminalResponse]:
    """Update an existing terminal."""
    with TerminalRepository() as repo:
        terminal = repo.find_by_id_and_organization(terminal_id, organization_id)
        if not terminal:
            return None

        # Validate branch if updating branch_id
        if dto.branch_id and dto.branch_id != str(terminal.branch_id):
            if not repo.validate_branch_exists(dto.branch_id, organization_id):
                raise ValueError(
                    f"Branch '{dto.branch_id}' does not exist or does not belong to this organization"
                )

        # Check code uniqueness if updating code
        if dto.code and dto.code != terminal.code:
            existing = repo.find_by_code_and_organization(dto.code, organization_id)
            if existing:
                raise ValueError(
                    f"Terminal code '{dto.code}' already exists in this organization"
                )

        # Check device_id uniqueness if updating device_id
        if dto.device_id and dto.device_id != terminal.device_id:
            existing_device = repo.find_by_device_id(dto.device_id)
            if existing_device:
                raise ValueError(
                    f"Device ID '{dto.device_id}' is already registered to another terminal"
                )

        # Update fields
        if dto.name is not None:
            terminal.name = dto.name
        if dto.code is not None:
            terminal.code = dto.code
        if dto.device_id is not None:
            terminal.device_id = dto.device_id
        if dto.is_active is not None:
            terminal.is_active = dto.is_active
        if dto.branch_id is not None:
            terminal.branch_id = uuid.UUID(dto.branch_id)

        terminal = repo.save(terminal)

    return _map_terminal(terminal)


def delete_terminal(organization_id: str, user_id: str, terminal_id: str) -> bool:
    """Delete a terminal if it has no active assignments."""
    with TerminalRepository() as repo:
        terminal = repo.find_by_id_and_organization(terminal_id, organization_id)
        if not terminal:
            return False

        # Check for active assignments
        if repo.has_active_assignments(terminal_id):
            raise ValueError(
                "Cannot delete terminal with active assignments. "
                "Please end all active assignments first."
            )

        return repo.delete(terminal_id)


def _map_terminal(terminal: Terminal) -> TerminalResponse:
    """Map Terminal model to TerminalResponse DTO."""
    return TerminalResponse(
        terminal_id=str(terminal.terminal_id),
        organization_id=terminal.organization_id,
        branch_id=str(terminal.branch_id),
        name=terminal.name,
        code=terminal.code,
        device_id=terminal.device_id,
        is_active=terminal.is_active,
        registered_at=terminal.registered_at.isoformat() if terminal.registered_at else "",
        last_seen_at=terminal.last_seen_at.isoformat() if terminal.last_seen_at else None,
        created_at=terminal.created_at.isoformat() if terminal.created_at else "",
        updated_at=terminal.updated_at.isoformat() if terminal.updated_at else "",
    )
