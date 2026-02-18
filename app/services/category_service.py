from __future__ import annotations

import logging
from typing import Optional
import uuid

from app.dtos.requests.category_request_dto import CategoryRequestDTO
from app.dtos.responses.category_dto import CategoryListResponse, CategoryResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository

logger = logging.getLogger(__name__)


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

        category = Category(
            id=str(uuid.uuid4()),
            organization_id=company_id,
            name=dto.name or "",
            slug=dto.slug or "",
            description=dto.description or "",
            background_color=dto.background_color or "#FFFFFF",
            button_color=dto.button_color or "#000000",
            image_1_url=dto.image_1_url,
            image_2_url=dto.image_2_url,
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
        if dto.image_1_url is not None:
            category.image_1_url = dto.image_1_url
        if dto.image_2_url is not None:
            category.image_2_url = dto.image_2_url
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
