from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Path, Query

from app.dtos.requests.create_sale_dto import CreateSaleDTO
from app.dtos.responses.sale_response_dto import SaleListResponse, SaleResponse
from app.services import sale_service


class SalesController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.post(
            "/api/organizations/{organization_id}/sales",
            response_model=SaleResponse,
            status_code=201,
            tags=["sales"],
            summary="Register a new sale",
            description="""Register a completed sale for an organization.

All fields use **snake_case**. Branch and terminal are identified by their **integer codes**.

**Required fields:**
- `branch_code`: Integer branch code (unique per org)
- `terminal_code`: Integer terminal code (unique per org)
- `activity_code`: Hacienda economic activity code
- `details`: List of line items (at least one)
- `payments`: List of payment method amounts (at least one)
- `subtotal`, `tax_amount`, `total_amount`: Sale totals

**Optional fields:**
- `assignment_id`: Links to the active cashier assignment
- `client_id`: UUID of the client (populates receiver from client record)
- `receiver`: Inline receiver data if no client selected
- `document_type`: Defaults to 1 (Boleta de Venta)
- `sale_condition_id`: Defaults to 1 (Contado)
- `notes`, `copy_emails`: Additional info
""",
        )
        async def create_sale(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            body: CreateSaleDTO,
        ) -> SaleResponse:
            try:
                return sale_service.create_sale(organization_id, x_user_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/sales",
            response_model=SaleListResponse,
            tags=["sales"],
            summary="List sales for an organization",
        )
        async def list_sales(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
            page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100),
        ) -> SaleListResponse:
            try:
                return sale_service.get_sales(organization_id, x_user_id, page=page, page_size=page_size)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/sales/{sale_id}",
            response_model=SaleResponse,
            tags=["sales"],
            summary="Get a specific sale with its line items",
        )
        async def get_sale(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            sale_id: Annotated[str, Path(description="Sale UUID")],
            x_user_id: Annotated[str, Header(description="User identifier from header")],
        ) -> SaleResponse:
            try:
                result = sale_service.get_sale(organization_id, x_user_id, sale_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Sale not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
