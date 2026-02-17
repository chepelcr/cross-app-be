from __future__ import annotations

import logging
from typing import Optional
import uuid

from app.dtos.requests.department_request_dto import CreateDepartmentDTO, UpdateDepartmentDTO
from app.dtos.responses.department_dto import DepartmentListResponse, DepartmentResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.department_search_filters import DepartmentSearchFilters
from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_departments(
    company_id: str,
    client_id: str,
    page: int = 1,
    page_size: int = 12,
    search: str = None,
) -> DepartmentListResponse:
    """Get paginated departments for a client with optional search filters."""
    search_filters = None
    order_by = None

    if search:
        filters, order_result = SearchUtils.parse_search_filter(
            search, Department, DepartmentSearchFilters
        )
        if filters:
            search_filters = filters
        if order_result:
            order_by = order_result

    client_uuid = uuid.UUID(client_id)

    with DepartmentRepository() as repo:
        departments, total = repo.find_all_by_client(
            company_id,
            client_uuid,
            search_filters=search_filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return DepartmentListResponse(
        data=[_map_department(d) for d in departments],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_department(department_id: uuid.UUID) -> Optional[DepartmentResponse]:
    """Get a single department by ID."""
    with DepartmentRepository() as repo:
        department = repo.find_by_id(department_id)
    if not department:
        return None
    return _map_department(department)


def create_department(
    company_id: str,
    client_id_str: str,
    dto: CreateDepartmentDTO,
) -> DepartmentResponse:
    """Create a new department."""
    client_id = uuid.UUID(client_id_str)

    with DepartmentRepository() as repo:
        department = Department(
            company_id=company_id,
            client_id=client_id,
            department_code=dto.department_code,
            name=dto.name,
            supplier_code=dto.supplier_code,
        )
        department = repo.save(department)

    return _map_department(department)


def update_department(
    department_id_str: str,
    dto: UpdateDepartmentDTO,
) -> Optional[DepartmentResponse]:
    """Update an existing department."""
    department_id = uuid.UUID(department_id_str)

    with DepartmentRepository() as repo:
        department = repo.find_by_id(department_id)
        if not department:
            return None

        if dto.department_code is not None:
            department.department_code = dto.department_code
        if dto.name is not None:
            department.name = dto.name
        if dto.supplier_code is not None:
            department.supplier_code = dto.supplier_code

        department = repo.save(department)

    return _map_department(department)


def update_department_status(
    department_id_str: str,
    status: int,
) -> Optional[DepartmentResponse]:
    """Update a department's status."""
    department_id = uuid.UUID(department_id_str)

    with DepartmentRepository() as repo:
        department = repo.find_by_id(department_id)
        if not department:
            return None

        department.status = status
        department = repo.save(department)

    return _map_department(department)


def delete_department(department_id_str: str) -> bool:
    """Soft delete a department."""
    department_id = uuid.UUID(department_id_str)

    with DepartmentRepository() as repo:
        return repo.soft_delete(department_id)


def _map_department(dept: Department) -> DepartmentResponse:
    return DepartmentResponse(
        departmentId=str(dept.department_id),
        companyId=dept.company_id,
        clientId=str(dept.client_id),
        departmentCode=dept.department_code,
        name=dept.name,
        supplierCode=dept.supplier_code,
    )
