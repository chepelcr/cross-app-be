from __future__ import annotations

import base64
import logging
import uuid
from typing import Optional

from app.dtos.requests.product_request_dto import ImageDTO, ProductRequestDTO
from app.dtos.responses.product_dto import CategoryResponse, ProductListResponse, ProductResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.product_search_filters import ProductSearchFilters
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.services.pdf_service import upload_file_to_s3
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def get_products(
    company_id: str,
    page: int = 1,
    page_size: int = 12,
    search: str = None,
) -> ProductListResponse:
    """Get paginated products for a company with optional search filters."""
    search_filters = None
    order_by = None

    if search:
        filters, order_result = SearchUtils.parse_search_filter(
            search, Product, ProductSearchFilters
        )
        if filters:
            search_filters = filters
        if order_result:
            order_by = order_result

    with ProductRepository() as repo:
        products, total = repo.find_all_by_company(
            company_id,
            search_filters=search_filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ProductListResponse(
        data=[_map_product(p) for p in products],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_product(product_id: str) -> Optional[ProductResponse]:
    """Get a single product by ID."""
    with ProductRepository() as repo:
        product = repo.find_by_id(product_id)
    if not product:
        return None
    return _map_product(product)


def create_product(organization_id: str, dto: ProductRequestDTO) -> ProductResponse:
    """Create a new product."""
    with ProductRepository() as repo:
        category_id = dto.category_id or repo._ensure_default_category(organization_id)

        product = Product(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=dto.name or dto.description or dto.internal_code or "",
            description=dto.description or dto.name or "",
            price=dto.price or 0,
            category_id=category_id,
            is_active=True,
            internal_code=dto.internal_code,
            original_code=dto.original_code,
            client_article_code=dto.client_article_code,
            code=dto.code,
            units_per_box=dto.units_per_box,
            sku=dto.sku,
        )
        repo.session.add(product)
        repo.session.flush()

        if dto.image and dto.image.data:
            url = _save_product_image(organization_id, product.id, dto.image)
            product.image_url = url
            repo.session.flush()

        return _map_product(product)


def update_product(
    organization_id: str, product_id: str, dto: ProductRequestDTO
) -> ProductResponse:
    """Update an existing product."""
    with ProductRepository() as repo:
        product = repo.find_by_id(product_id)
        if not product:
            raise LookupError(f"Product '{product_id}' not found")
        if product.organization_id != organization_id:
            raise LookupError(f"Product '{product_id}' not found for organization {organization_id}")

        if dto.internal_code is not None:
            product.internal_code = dto.internal_code
        if dto.original_code is not None:
            product.original_code = dto.original_code
        if dto.client_article_code is not None:
            product.client_article_code = dto.client_article_code
        if dto.code is not None:
            product.code = dto.code
        if dto.name is not None:
            product.name = dto.name
        if dto.description is not None:
            product.description = dto.description
        if dto.units_per_box is not None:
            product.units_per_box = dto.units_per_box
        if dto.price is not None:
            product.price = dto.price
        if dto.sku is not None:
            product.sku = dto.sku
        if dto.category_id is not None:
            product.category_id = dto.category_id

        if dto.image and dto.image.data:
            url = _save_product_image(organization_id, product.id, dto.image)
            product.image_url = url

        repo.save(product)
        return _map_product(product)


def update_product_status(
    organization_id: str, product_id: str, status: int
) -> ProductResponse:
    """Update a product's active status."""
    with ProductRepository() as repo:
        product = repo.find_by_id(product_id)
        if not product:
            raise LookupError(f"Product '{product_id}' not found")
        if product.organization_id != organization_id:
            raise LookupError(f"Product '{product_id}' not found for organization {organization_id}")

        product.is_active = status == 1
        repo.save(product)
        return _map_product(product)


def _save_product_image(organization_id: str, product_id: str, image: ImageDTO) -> str:
    """Validate, decode, and upload a product image to S3."""
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
            f"Image size ({len(decoded)} bytes) exceeds maximum allowed ({MAX_IMAGE_SIZE // (1024 * 1024)}MB)"
        )

    key = f"organizations/{organization_id}/products/{product_id}/image.{ext}"
    return upload_file_to_s3(decoded, key, content_type)


def _map_product(product: Product) -> ProductResponse:
    category = None
    if product.category:
        category = CategoryResponse(
            categoryId=product.category_id,
            name=product.category.name if hasattr(product.category, "name") else None,
        )

    return ProductResponse(
        productId=product.id,
        companyId=product.organization_id,
        internalCode=product.internal_code,
        originalCode=product.original_code,
        clientArticleCode=product.client_article_code,
        code=product.code,
        name=product.name,
        description=product.description,
        unitsPerBox=product.units_per_box,
        imageUrl=product.image_url,
        category=category,
    )
