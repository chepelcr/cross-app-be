from __future__ import annotations

import base64
import logging
from typing import Optional
import uuid

from app.dtos.requests.category_request_dto import CategoryRequestDTO
from app.dtos.files import ImageDTO
from app.dtos.responses.category_dto import CategoryListResponse, CategoryResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.services.pdf_service import upload_file_to_s3

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def get_categories(
    company_id: str,
    page: int = 1,
    page_size: int = 12,
) -> CategoryListResponse:
    """Get paginated categories for a company."""
    with CategoryRepository() as repo:
        categories, total = repo.find_all_by_company(
            company_id,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return CategoryListResponse(
        data=[_map_category(c) for c in categories],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_category(company_id: str, category_id: str) -> Optional[CategoryResponse]:
    """Get a single category by ID."""
    with CategoryRepository() as repo:
        category = repo.find_by_id_and_company(category_id, company_id)
    if not category:
        return None
    return _map_category(category)


def create_category(
    company_id: str,
    dto: CategoryRequestDTO,
) -> CategoryResponse:
    """Create a new category."""
    with CategoryRepository() as repo:
        # Check slug uniqueness
        if dto.slug:
            existing = repo.find_by_slug_and_company(dto.slug, company_id)
            if existing:
                raise ValueError("Category slug already exists")

        category_id = str(uuid.uuid4())

        # Handle image uploads
        image_1_url = None
        image_2_url = None
        if dto.image_1:
            image_1_url = _save_category_image(company_id, category_id, dto.image_1, "image1")
        if dto.image_2:
            image_2_url = _save_category_image(company_id, category_id, dto.image_2, "image2")

        category = Category(
            id=category_id,
            organization_id=company_id,
            name=dto.name or "",
            slug=dto.slug or "",
            description=dto.description or "",
            background_color=dto.background_color or "#FFFFFF",
            button_color=dto.button_color or "#000000",
            image_1_url=image_1_url,
            image_2_url=image_2_url,
            is_active=True,
            sort_order=dto.sort_order or 0,
        )
        category = repo.save(category)

    return _map_category(category)


def update_category(
    company_id: str,
    category_id: str,
    dto: CategoryRequestDTO,
) -> Optional[CategoryResponse]:
    """Update an existing category."""
    with CategoryRepository() as repo:
        category = repo.find_by_id_and_company(category_id, company_id)
        if not category:
            return None

        # Check slug uniqueness if updating
        if dto.slug and dto.slug != category.slug:
            existing = repo.find_by_slug_and_company(dto.slug, company_id)
            if existing:
                raise ValueError("Category slug already exists")

        if dto.name is not None:
            category.name = dto.name
        if dto.slug is not None:
            category.slug = dto.slug
        if dto.description is not None:
            category.description = dto.description
        if dto.background_color is not None:
            category.background_color = dto.background_color
        if dto.button_color is not None:
            category.button_color = dto.button_color
        if dto.image_1 is not None:
            category.image_1_url = _save_category_image(company_id, category_id, dto.image_1, "image1")
        if dto.image_2 is not None:
            category.image_2_url = _save_category_image(company_id, category_id, dto.image_2, "image2")
        if dto.sort_order is not None:
            category.sort_order = dto.sort_order

        category = repo.save(category)

    return _map_category(category)


def update_category_status(
    company_id: str,
    category_id: str,
    status: int,
) -> Optional[CategoryResponse]:
    """Update a category's active status."""
    with CategoryRepository() as repo:
        category = repo.find_by_id_and_company(category_id, company_id)
        if not category:
            return None

        category.is_active = status == 1
        category = repo.save(category)

    return _map_category(category)


def delete_category(company_id: str, category_id: str) -> bool:
    """Delete a category."""
    with CategoryRepository() as repo:
        category = repo.find_by_id_and_company(category_id, company_id)
        if not category:
            return False
        return repo.delete(category_id)


def _save_category_image(organization_id: str, category_id: str, image: ImageDTO, image_name: str) -> str:
    """Validate, decode, and upload a category image to S3."""
    if not image.data:
        raise ValueError("Image data is empty")

    content_type = (image.content_type or "").lower().strip()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"Invalid image type '{content_type}'. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )

    ext = ALLOWED_IMAGE_TYPES[content_type]

    # Strip data URL prefix if present (e.g. "data:image/png;base64,...")
    data = image.data
    if data.startswith("data:"):
        if "," in data:
            data = data.split(",", 1)[1]

    try:
        decoded = base64.b64decode(data)
    except Exception:
        raise ValueError("Invalid base64 image data")

    if len(decoded) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image size ({len(decoded)} bytes) exceeds maximum allowed "
            f"({MAX_IMAGE_SIZE // (1024 * 1024)}MB)"
        )

    # Use custom filename if provided, otherwise use default
    filename = image.name if image.name else f"{image_name}.{ext}"
    key = f"organizations/{organization_id}/categories/{category_id}/{filename}"
    return upload_file_to_s3(decoded, key, content_type)


def _map_category(category: Category) -> CategoryResponse:
    return CategoryResponse(
        categoryId=category.id,
        organizationId=category.organization_id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        backgroundColor=category.background_color,
        buttonColor=category.button_color,
        image1Url=category.image_1_url,
        image2Url=category.image_2_url,
        isActive=category.is_active,
        sortOrder=category.sort_order,
    )
