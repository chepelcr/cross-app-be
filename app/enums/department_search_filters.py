from __future__ import annotations

from enum import Enum
from typing import Optional, Set


ENTITY_DEPARTMENT = "Department"
ENTITY_ALL = {ENTITY_DEPARTMENT}


class DepartmentSearchFilters(Enum):
    """
    Search filters for Department entity.

    Format: (entity_field, json_field, is_join, join_field, is_controller, entities, allows_like, allows_between)
    """

    DEPARTMENT_CODE = ("department_code", "departmentCode", False, None, True, ENTITY_ALL, False, False)
    NAME = ("name", "name", False, None, True, ENTITY_ALL, True, False)
    SUPPLIER_CODE = ("supplier_code", "supplierCode", False, None, True, ENTITY_ALL, False, False)
    ORDER_BY = (None, "orderBy", False, None, False, ENTITY_ALL, False, False)

    def __init__(
        self,
        entity_field: Optional[str],
        json_field: Optional[str],
        is_join_field: bool,
        join_field: Optional[str],
        is_controller_filter: bool,
        applicable_entities: Optional[Set[str]] = None,
        allows_like: bool = False,
        allows_between: bool = False,
    ) -> None:
        self._entity_field = entity_field
        self._json_field = json_field
        self._is_join_field = is_join_field
        self._join_field = join_field
        self._is_controller_filter = is_controller_filter
        self._applicable_entities = applicable_entities or ENTITY_ALL
        self._allows_like = allows_like
        self._allows_between = allows_between

    @property
    def entity_field(self) -> Optional[str]:
        return self._entity_field

    @property
    def json_field(self) -> Optional[str]:
        return self._json_field

    @property
    def is_join_field(self) -> bool:
        return self._is_join_field

    @property
    def join_field(self) -> Optional[str]:
        return self._join_field

    @property
    def is_controller_filter(self) -> bool:
        return self._is_controller_filter

    @property
    def allows_like(self) -> bool:
        return self._allows_like

    @property
    def allows_between(self) -> bool:
        return self._allows_between

    @classmethod
    def get_filter_by_json_field(cls, json_field: str) -> Optional[DepartmentSearchFilters]:
        for f in cls:
            if f.json_field and f.json_field == json_field:
                return f
        return None
