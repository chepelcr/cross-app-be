from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.dtos.requests.table_request_dto import (
    TableCreateRequestDTO,
    TableUpdateRequestDTO,
)
from app.dtos.responses.table_dto import TableListResponse, TableResponse
from app.models.table import Table
from app.repositories.branch_repository import BranchRepository
from app.repositories.table_repository import TableRepository

logger = logging.getLogger(__name__)


def _map(table: Table) -> TableResponse:
    return TableResponse(
        table_id=str(table.table_id),
        organization_id=table.organization_id,
        branch_id=str(table.branch_id),
        code=table.code,
        name=table.name,
        seats=table.seats,
        zone=table.zone,
        sort_order=table.sort_order or 0,
        is_dynamic=bool(table.is_dynamic),
        opened_by=table.opened_by,
        held_document_id=table.held_document_id,
        status=table.status,
    )


def _resolve_branch_id(repo: TableRepository, organization_id: str, branch_code: int) -> uuid.UUID:
    """Branches are addressed by their integer code, not their UUID (TSR-149).

    The POS session only ever holds `branch_code`, so resolving here keeps the
    UUID an internal detail instead of pushing it into the client.
    """
    branch_repo = BranchRepository.from_session(repo.session)
    branch = branch_repo.find_by_code_and_organization(branch_code, organization_id)
    if not branch:
        raise LookupError(f"Branch '{branch_code}' not found in this organization")
    return branch.branch_id


def get_tables(
    organization_id: str, branch_code: int, include_dynamic: bool = True
) -> TableListResponse:
    with TableRepository() as repo:
        branch_id = _resolve_branch_id(repo, organization_id, branch_code)
        tables = repo.find_all_by_branch(
            organization_id, branch_id, include_dynamic=include_dynamic
        )
    return TableListResponse(data=[_map(t) for t in tables])


def create_table(
    organization_id: str, branch_code: int, user_id: str, dto: TableCreateRequestDTO
) -> TableResponse:
    """Add a mesa to the floor plan, or open a bar tab.

    Same call for both: a tab is a dynamic table, which is why the bar vertical
    needed no second mechanism.
    """
    with TableRepository() as repo:
        branch_uuid = _resolve_branch_id(repo, organization_id, branch_code)
        if repo.find_by_branch_and_code(branch_uuid, dto.code):
            raise ValueError(f"Table code '{dto.code}' already exists in this branch")

        table = Table(
            table_id=uuid.uuid4(),
            organization_id=organization_id,
            branch_id=branch_uuid,
            code=dto.code,
            name=dto.name,
            seats=dto.seats,
            zone=dto.zone,
            sort_order=dto.sort_order if dto.sort_order is not None else 0,
            is_dynamic=dto.is_dynamic,
            # Only a tab records who opened it — a floor-plan table belongs to
            # the room, not to a shift.
            opened_by=user_id if dto.is_dynamic else None,
            created_by=user_id,
        )
        table = repo.save(table)
        return _map(table)


def update_table(
    organization_id: str, table_id: str, dto: TableUpdateRequestDTO
) -> TableResponse:
    with TableRepository() as repo:
        table = repo.find_by_id_and_organization(uuid.UUID(table_id), organization_id)
        if not table:
            raise LookupError(f"Table '{table_id}' not found")

        for field in ("name", "seats", "zone", "sort_order"):
            value = getattr(dto, field)
            if value is not None:
                setattr(table, field, value)

        # Sent explicitly (including null) to hold or release the table, so it
        # is assigned unconditionally rather than skipped when null.
        if "held_document_id" in dto.model_fields_set:
            table.held_document_id = dto.held_document_id

        table.updated_on = datetime.now(timezone.utc)
        table = repo.save(table)
        return _map(table)


def delete_table(organization_id: str, table_id: str) -> None:
    """Remove a mesa, or close a tab.

    Soft delete: an order may still point at the table it was taken at, and
    breaking that link would break the receipt.
    """
    with TableRepository() as repo:
        table = repo.find_by_id_and_organization(uuid.UUID(table_id), organization_id)
        if not table:
            raise LookupError(f"Table '{table_id}' not found")
        if table.held_document_id:
            raise ValueError(
                "Table still holds an open order — settle or move it before closing"
            )
        repo.soft_delete(table)
