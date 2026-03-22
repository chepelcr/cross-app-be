from __future__ import annotations

from typing import Set

from app.enums.base_search_filter import BaseSearchFilter


ENTITY_PRODUCT = "Product"
ENTITY_ALL = {ENTITY_PRODUCT}


class ProductSearchFilters(BaseSearchFilter):
    """
    Search filters for Product entity.

    Format: (entity_field, json_field, is_join, join_field, is_controller, entities, allows_like, allows_between, sortable, always_like)
    """

    DESCRIPTION = ("description", "description", False, None, True, ENTITY_ALL, True, False, True, True)
    CODE = ("codes", "code", False, None, True, ENTITY_ALL, False, False, False, False)
    NAME = ("name", "name", False, None, True, ENTITY_ALL, True, False, True, True)
    CATEGORY_ID = ("category_id", "categoryId", False, None, True, ENTITY_ALL, False, False, False, False)
    CATEGORY_NAME = ("name", "categoryName", True, "category", True, ENTITY_ALL, True, False, False, True)
    STATUS = ("status", "status", False, None, True, ENTITY_ALL, False, False, False, False)
    PRICE = ("price", "price", False, None, True, ENTITY_ALL, False, True, True, False)
    SALE_PRICE = ("sale_price", "salePrice", False, None, True, ENTITY_ALL, False, True, True, False)
    CREATED_ON = ("created_on", "createdOn", False, None, True, ENTITY_ALL, False, False, True, False)
    UPDATED_ON = ("updated_on", "updatedOn", False, None, True, ENTITY_ALL, False, False, True, False)
    ORDER_BY = (None, "orderBy", False, None, False, ENTITY_ALL, False, False, False, False)
