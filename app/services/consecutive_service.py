from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.dtos.requests.consecutive_request_dto import ConsecutiveCreateRequestDTO
from app.dtos.responses.consecutive_dto import ConsecutiveListResponse, ConsecutiveResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.consecutive_search_filters import ConsecutiveSearchFilters
from app.models.consecutive import Consecutive
from app.repositories.consecutive_repository import ConsecutiveRepository
from app.repositories.document_type_repository import DocumentTypeRepository
from app.repositories.terminal_repository import TerminalRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_consecutives(
    organization_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 12,
    search: Optional[str] = None,
) -> ConsecutiveListResponse:
    """Get all consecutives for an organization with pagination and optional filters."""
    filters, order_by = (
        SearchUtils.parse_search_filter(search, Consecutive, ConsecutiveSearchFilters)
        if search
        else ([], None)
    )

    with ConsecutiveRepository() as repo:
        items, total = repo.find_all_paginated(
            organization_id,
            filters=filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ConsecutiveListResponse(
        data=[_map_consecutive(c) for c in items],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total_elements=total,
            total_pages=total_pages,
        ),
    )


def get_consecutive(
    organization_id: str, user_id: str, consecutive_id: str
) -> Optional[ConsecutiveResponse]:
    """Get a single consecutive by ID."""
    with ConsecutiveRepository() as repo:
        c = repo.find_by_id_and_org(consecutive_id, organization_id)
    return _map_consecutive(c) if c else None


def create_consecutive(
    organization_id: str,
    user_id: str,
    dto: ConsecutiveCreateRequestDTO,
) -> ConsecutiveResponse:
    """Create a new consecutive sequence counter."""
    # Validate terminal belongs to org
    with TerminalRepository() as t_repo:
        terminal = t_repo.find_by_id_and_organization(dto.terminal_id, organization_id)
    if not terminal:
        raise ValueError(f"Terminal {dto.terminal_id} not found in organization")

    # Validate document type exists
    with DocumentTypeRepository() as dt_repo:
        doc_type = dt_repo.find_by_id(dto.document_type_id)
    if not doc_type:
        raise ValueError(f"Document type {dto.document_type_id} not found")

    with ConsecutiveRepository() as repo:
        # Check uniqueness
        existing = repo.find_by_terminal_and_doc_type(
            dto.terminal_id, dto.document_type_id, organization_id
        )
        if existing:
            raise ValueError(
                f"Consecutive for terminal {dto.terminal_id} and document type "
                f"{dto.document_type_id} already exists"
            )

        consecutive = Consecutive(
            organization_id=organization_id,
            terminal_id=uuid.UUID(dto.terminal_id),
            document_type_id=dto.document_type_id,
            current_number=(
                dto.initial_number
                if hasattr(dto, 'initial_number') and dto.initial_number is not None
                else 0
            ),
            created_by=user_id,
        )
        saved = repo.save(consecutive)

    return _map_consecutive(saved)


def get_next_number(
    organization_id: str, terminal_id: str, document_type_id: int
) -> Optional[ConsecutiveResponse]:
    """Atomically increment and return the next consecutive number."""
    with ConsecutiveRepository() as repo:
        existing = repo.find_by_terminal_and_doc_type(
            terminal_id, document_type_id, organization_id
        )
        if not existing:
            return None
        updated = repo.increment_and_get(str(existing.consecutive_id), organization_id)
    return _map_consecutive(updated) if updated else None


def update_consecutive_status(
    organization_id: str,
    user_id: str,
    consecutive_id: str,
    status: int,
) -> Optional[ConsecutiveResponse]:
    """Update the status of a consecutive. Status 3 (Deleted) sets deleted_on."""
    with ConsecutiveRepository() as repo:
        consecutive = repo.find_by_id_and_org(consecutive_id, organization_id)
        if not consecutive:
            return None

        consecutive.status = status
        if status == 3:
            consecutive.deleted_on = datetime.now(timezone.utc)

        repo.save(consecutive)

    return _map_consecutive(consecutive)


def _map_consecutive(c: Consecutive) -> ConsecutiveResponse:
    """Map Consecutive model to ConsecutiveResponse DTO."""
    return ConsecutiveResponse(
        consecutive_id=str(c.consecutive_id),
        organization_id=c.organization_id,
        terminal_id=str(c.terminal_id),
        document_type_id=c.document_type_id,
        current_number=c.current_number,
        created_at=c.created_on.isoformat() if c.created_on else None,
        updated_at=c.updated_on.isoformat() if c.updated_on else None,
        created_by=c.created_by,
    )
