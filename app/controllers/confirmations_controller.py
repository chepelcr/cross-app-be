from typing import Annotated, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.confirmation_request_dto import (
    CreateConfirmationDTO,
    UpdateConfirmationDTO,
)
from app.dtos.requests.status_request_dto import StatusRequestDTO
from app.dtos.responses.confirmation_response_dto import (
    ConfirmationListResponse,
    ConfirmationResponse,
)
from app.services import confirmation_service


class ConfirmationsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):
        @app.post(
            "/api/organizations/{organization_id}/confirmations",
            response_model=ConfirmationResponse,
            tags=["confirmations"],
            summary="Create a confirmation and link orders",
        )
        async def create_confirmation(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: CreateConfirmationDTO = Body(...),
        ):
            try:
                return confirmation_service.create_confirmation(organization_id, body)
            except ValueError as e:
                raise HTTPException(status_code=409, detail=str(e))
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.put(
            "/api/organizations/{organization_id}/confirmations/{confirmation_number}",
            response_model=ConfirmationResponse,
            tags=["confirmations"],
            summary="Update confirmation details and/or add more orders",
        )
        async def update_confirmation(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            confirmation_number: Annotated[str, Path(description="Confirmation number")],
            body: UpdateConfirmationDTO = Body(...),
        ):
            try:
                return confirmation_service.update_confirmation(
                    organization_id, confirmation_number, body
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/confirmations/{confirmation_number}",
            response_model=ConfirmationResponse,
            tags=["confirmations"],
            summary="Get a confirmation by number",
        )
        async def get_confirmation(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            confirmation_number: Annotated[str, Path(description="Confirmation number")],
        ):
            try:
                return confirmation_service.get_confirmation(
                    organization_id, confirmation_number
                )
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/confirmations",
            response_model=ConfirmationListResponse,
            tags=["confirmations"],
            summary="List confirmations for an organization",
        )
        async def list_confirmations(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            page: int = Query(1, ge=1, description="Page number"),
            page_size: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            return confirmation_service.list_confirmations(
                organization_id, page=page, page_size=page_size
            )

        @app.patch(
            "/api/organizations/{organization_id}/confirmations/{confirmation_number}/status",
            response_model=ConfirmationResponse,
            tags=["confirmations"],
            summary="Update status of confirmation and its orders (3=shipped triggers email)",
        )
        async def update_confirmation_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            confirmation_number: Annotated[str, Path(description="Confirmation number")],
            body: StatusRequestDTO = Body(...),
        ):
            try:
                return confirmation_service.update_confirmation_status(
                    organization_id, confirmation_number, body.status
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/confirmations/{confirmation_number}/orders/{document_number}",
            response_model=ConfirmationResponse,
            tags=["confirmations"],
            summary="Remove an order from a confirmation",
        )
        async def remove_order_from_confirmation(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            confirmation_number: Annotated[str, Path(description="Confirmation number")],
            document_number: Annotated[str, Path(description="Order document number")],
        ):
            try:
                return confirmation_service.remove_order_from_confirmation(
                    organization_id, confirmation_number, document_number
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except LookupError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
