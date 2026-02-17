from __future__ import annotations

import logging
from typing import Optional
import uuid

from app.dtos.requests.client_request_dto import ClientRequestDTO
from app.dtos.responses.client_dto import ClientListResponse, ClientResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.client_search_filters import ClientSearchFilters
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


def get_clients(
    company_id: str,
    page: int = 1,
    page_size: int = 12,
    search: str = None,
) -> ClientListResponse:
    """Get paginated clients for a company with optional search filters."""
    search_filters = None
    order_by = None

    if search:
        filters, order_result = SearchUtils.parse_search_filter(
            search, Client, ClientSearchFilters
        )
        if filters:
            search_filters = filters
        if order_result:
            order_by = order_result

    with ClientRepository() as repo:
        clients, total = repo.find_all_by_company(
            company_id,
            search_filters=search_filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ClientListResponse(
        data=[_map_client(c) for c in clients],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_client(client_id: uuid.UUID) -> Optional[ClientResponse]:
    """Get a single client by ID."""
    with ClientRepository() as repo:
        client = repo.find_by_id(client_id)
    if not client:
        return None
    return _map_client(client)


def create_client(
    company_id: str,
    dto: "ClientRequestDTO",
) -> ClientResponse:
    """Create a new client."""
    with ClientRepository() as repo:
        client = Client(
            company_id=company_id,
            client_name=dto.client_name,
            client_gln=dto.client_gln,
        )
        client = repo.save(client)

    return _map_client(client)


def update_client(
    client_id_str: str,
    dto: "ClientRequestDTO",
) -> Optional[ClientResponse]:
    """Update an existing client."""
    client_id = uuid.UUID(client_id_str)

    with ClientRepository() as repo:
        client = repo.find_by_id(client_id)
        if not client:
            return None

        if dto.client_name is not None:
            client.client_name = dto.client_name
        if dto.client_gln is not None:
            client.client_gln = dto.client_gln

        client = repo.save(client)

    return _map_client(client)


def update_client_status(
    client_id_str: str,
    status: int,
) -> Optional[ClientResponse]:
    """Update a client's status."""
    client_id = uuid.UUID(client_id_str)

    with ClientRepository() as repo:
        client = repo.find_by_id(client_id)
        if not client:
            return None

        client.status = status
        client = repo.save(client)

    return _map_client(client)


def _map_client(client: Client) -> ClientResponse:
    return ClientResponse(
        clientId=str(client.client_id),
        companyId=client.company_id,
        clientName=client.client_name,
        clientGln=client.client_gln,
    )
