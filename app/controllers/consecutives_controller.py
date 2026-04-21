from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.consecutive_request_dto import ConsecutiveCreateRequestDTO
from app.dtos.requests.product_status_request_dto import ProductStatusRequestDTO
from app.dtos.responses.consecutive_dto import ConsecutiveListResponse, ConsecutiveResponse
from app.repositories.consecutive_repository import ConsecutiveRepository
from app.services import consecutive_service
from app.services.consecutive_service import _map_consecutive


class ConsecutivesController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/consecutives",
            response_model=ConsecutiveListResponse,
            tags=["consecutives"],
            summary="List consecutives with pagination and search",
        )
        async def list_consecutives(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            search: Optional[str] = Query(None, description="Search filter (field:value syntax)"),
            page: int = Query(1, ge=1),
            pageSize: int = Query(12, ge=1, le=100),
        ):
            try:
                return consecutive_service.get_consecutives(
                    organization_id, x_user_id, page=page, page_size=pageSize, search=search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/consecutives/{consecutive_id}",
            response_model=ConsecutiveResponse,
            tags=["consecutives"],
            summary="Get a specific consecutive by ID",
        )
        async def get_consecutive(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            consecutive_id: Annotated[str, Path(description="Consecutive ID")],
        ):
            try:
                result = consecutive_service.get_consecutive(organization_id, x_user_id, consecutive_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Consecutive not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/terminals/{terminal_id}/consecutives/{document_type_id}",
            response_model=ConsecutiveResponse,
            tags=["consecutives"],
            summary="Get (and optionally increment) a consecutive for a terminal and document type",
        )
        async def get_terminal_consecutive(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            terminal_id: Annotated[str, Path(description="Terminal ID")],
            document_type_id: Annotated[int, Path(description="Document type ID")],
            increment: bool = Query(False, description="Atomically increment the counter before returning"),
        ):
            try:
                if increment:
                    result = consecutive_service.get_next_number(organization_id, terminal_id, document_type_id)
                else:
                    with ConsecutiveRepository() as repo:
                        c = repo.find_by_terminal_and_doc_type(terminal_id, document_type_id, organization_id)
                    result = _map_consecutive(c) if c else None
                if not result:
                    raise HTTPException(status_code=404, detail="Consecutive not found for this terminal and document type")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/consecutives",
            response_model=ConsecutiveResponse,
            status_code=201,
            tags=["consecutives"],
            summary="Create a new consecutive counter",
        )
        async def create_consecutive(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: ConsecutiveCreateRequestDTO,
        ):
            try:
                return consecutive_service.create_consecutive(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/consecutives/{consecutive_id}/status",
            response_model=ConsecutiveResponse,
            tags=["consecutives"],
            summary="Update consecutive status",
        )
        async def update_consecutive_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],

            x_user_id: Annotated[str, Header(description="User identifier from header")],
            consecutive_id: Annotated[str, Path(description="Consecutive ID")],
            body: ProductStatusRequestDTO,
        ):
            try:
                result = consecutive_service.update_consecutive_status(
                    organization_id, x_user_id, consecutive_id, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Consecutive not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
