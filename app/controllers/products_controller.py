from __future__ import annotations

from typing import Annotated, Optional

from fastapi import FastAPI, HTTPException, Path, Query

from app.dtos.responses.product_dto import ProductListResponse, ProductResponse
from app.services import product_service


class ProductsController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/products",
            response_model=ProductListResponse,
            tags=["products"],
            summary="Get all products for an organization",
            description="""Get a paginated list of products with optional search filters.

**Search filters**
- `internalCode`: Internal product code
- `description`: Product description (supports wildcards)
- `originalCode`: Original product code
- `code`: Product code
- `name`: Product name (supports wildcards)

**Sorting**
- `orderBy>field` (Ascending)
- `orderBy<field` (Descending)
- Sortable fields: `internalCode`, `description`, `originalCode`, `code`, `name`

**Example:** `name:*shampoo*,orderBy>internalCode`
""",
        )
        async def list_products(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            search: Optional[str] = Query(
                None,
                description=(
                    "Search filter string. Syntax: field:value,field2:value2. "
                    "Supports operators: : (equal), ! (not equal), > (greater), < (less), ~ (like). "
                    "Example: name:*shampoo*,orderBy>internalCode"
                ),
            ),
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            pageSize: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            try:
                return product_service.get_products(
                    organization_id, page, pageSize, search
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/products/{product_id}",
            response_model=ProductResponse,
            tags=["products"],
            summary="Get a specific product by ID",
        )
        async def get_product(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            product_id: Annotated[str, Path(description="Product ID")],
        ):
            try:
                result = product_service.get_product(product_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Product not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
