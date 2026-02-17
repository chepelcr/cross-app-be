from __future__ import annotations

import logging
from typing import Optional

from app.dtos.responses.product_dto import CategoryResponse, ProductListResponse, ProductResponse
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.product_search_filters import ProductSearchFilters
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)


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
        category=category,
    )
