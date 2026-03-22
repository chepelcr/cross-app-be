from __future__ import annotations

from typing import Set

from app.enums.base_search_filter import BaseSearchFilter


ENTITY_ORDER = "Order"
ENTITY_ALL = {ENTITY_ORDER}


class SearchFilters(BaseSearchFilter):
    """
    Search filters for Order entity.

    Format: (entity_field, json_field, is_join, join_field, is_controller, entities, allows_like, allows_between, sortable, always_like)
    """

    DOCUMENT_NUMBER = ("document_number", "documentNumber", False, None, True, ENTITY_ALL, True, False, True, True)
    CLIENT_NAME = ("client", "clientName", True, "client_name", True, ENTITY_ALL, True, False, False, True)
    SUPPLIER_NAME = ("organization", "supplierName", True, "name", True, ENTITY_ALL, True, False, False, True)
    DELIVERY_DATE = ("delivery_date", "deliveryDate", False, None, True, ENTITY_ALL, False, True, True, False)
    CREATION_DATE = ("creation_date", "creationDate", False, None, True, ENTITY_ALL, False, True, True, False)
    ORDER_STATUS = ("order_status", "orderStatus", False, None, True, ENTITY_ALL, False, False, True, False)
    DELIVER_TO_CODE = ("deliver_to_store", "deliverToCode", True, "store_code", True, ENTITY_ALL, False, False, False, False)
    DELIVER_TO_NAME = ("deliver_to_store", "deliverToName", True, "store_name", True, ENTITY_ALL, True, False, False, True)
    CONFIRMATION_NUMBER = ("confirmation_number", "confirmationNumber", False, None, True, ENTITY_ALL, True, False, True, True)
    CREATED_ON = ("created_on", "createdOn", False, None, True, ENTITY_ALL, False, False, True, False)
    UPDATED_ON = ("updated_on", "updatedOn", False, None, True, ENTITY_ALL, False, False, True, False)
    ORDER_BY = (None, "orderBy", False, None, False, ENTITY_ALL, False, False, False, False)
