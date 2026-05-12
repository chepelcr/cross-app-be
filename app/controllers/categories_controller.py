from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query

from app.dtos.requests.category_request_dto import CategoryRequestDTO
from app.dtos.requests.status_request_dto import StatusRequestDTO
from app.dtos.responses.category_dto import CategoryListResponse, CategoryResponse
from app.services import category_service


class CategoriesController:
    def __init__(self, app: FastAPI):
        self.register_routes(app)

    def register_routes(self, app: FastAPI):

        @app.get(
            "/api/organizations/{organization_id}/categories",
            response_model=CategoryListResponse,
            tags=["categories"],
            summary="Get all categories for an organization",
        )
        async def list_categories(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            page: int = Query(1, ge=1, description="Page number (1-indexed)"),
            page_size: int = Query(12, ge=1, le=100, description="Items per page"),
        ):
            try:
                return category_service.get_categories(organization_id, page, page_size)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.get(
            "/api/organizations/{organization_id}/categories/{category_id}",
            response_model=CategoryResponse,
            tags=["categories"],
            summary="Get a specific category by ID",
        )
        async def get_category(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            category_id: Annotated[str, Path(description="Category ID")],
        ):
            try:
                result = category_service.get_category(organization_id, category_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Category not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post(
            "/api/organizations/{organization_id}/categories",
            response_model=CategoryResponse,
            status_code=201,
            tags=["categories"],
            summary="Create a new category",
            description="""Create a new category for an organization.

Optional `image1` and `image2` fields can be included with base64-encoded image data.
Supported image formats: PNG, JPEG, GIF, WEBP. Max size: 5MB per image.
""",
        )
        async def create_category(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            body: CategoryRequestDTO,
        ):
            try:
                return category_service.create_category(organization_id, body)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.put(
            "/api/organizations/{organization_id}/categories/{category_id}",
            response_model=CategoryResponse,
            tags=["categories"],
            summary="Update an existing category",
            description="""Update a category. Only provided fields are updated.

Optional `image1` and `image2` fields can be included with base64-encoded image data.
Supported image formats: PNG, JPEG, GIF, WEBP. Max size: 5MB per image.
""",
        )
        async def update_category(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            category_id: Annotated[str, Path(description="Category ID")],
            body: CategoryRequestDTO,
        ):
            try:
                result = category_service.update_category(organization_id, category_id, body)
                if not result:
                    raise HTTPException(status_code=404, detail="Category not found")
                return result
            except HTTPException:
                raise
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.patch(
            "/api/organizations/{organization_id}/categories/{category_id}",
            response_model=CategoryResponse,
            tags=["categories"],
            summary="Update category status",
        )
        async def update_category_status(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            category_id: Annotated[str, Path(description="Category ID")],
            body: StatusRequestDTO = Body(...),
        ):
            try:
                result = category_service.update_category_status(
                    organization_id, category_id, body.status
                )
                if not result:
                    raise HTTPException(status_code=404, detail="Category not found")
                return result
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.delete(
            "/api/organizations/{organization_id}/categories/{category_id}",
            tags=["categories"],
            summary="Delete a category",
            status_code=204,
        )
        async def delete_category(
            organization_id: Annotated[str, Path(description="Organization identifier")],
            category_id: Annotated[str, Path(description="Category ID")],
        ):
            try:
                deleted = category_service.delete_category(organization_id, category_id)
                if not deleted:
                    raise HTTPException(status_code=404, detail="Category not found")
                return None
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
