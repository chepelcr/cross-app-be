from __future__ import annotations

from enum import Enum
from typing import Optional, Set


ENTITY_BRANCH = "Branch"
ENTITY_ALL = {ENTITY_BRANCH}


class BranchSearchFilters(Enum):
    NAME = ("name", "name", False, None, True, ENTITY_ALL, True, False, True, False)
    CODE = ("code", "code", False, None, True, ENTITY_ALL, True, False, True, False)
    TYPE = ("type", "type", False, None, True, ENTITY_ALL, False, False, True, False)
    STATUS = ("status", "status", False, None, True, ENTITY_ALL, False, False, True, False)
    CREATED_ON = ("created_on", "created_on", False, None, True, ENTITY_ALL, False, False, True, False)
    ORDER_BY = (None, "order_by", False, None, False, ENTITY_ALL, False, False, False, False)

    def __init__(self, entity_field, json_field, is_join_field, join_field, is_controller_filter,
                 applicable_entities=None, allows_like=False, allows_between=False, sortable=False, always_like=False):
        self._entity_field = entity_field
        self._json_field = json_field
        self._is_join_field = is_join_field
        self._join_field = join_field
        self._is_controller_filter = is_controller_filter
        self._applicable_entities = applicable_entities or ENTITY_ALL
        self._allows_like = allows_like
        self._allows_between = allows_between
        self._sortable = sortable
        self._always_like = always_like

    @property
    def entity_field(self): return self._entity_field
    @property
    def json_field(self): return self._json_field
    @property
    def is_join_field(self): return self._is_join_field
    @property
    def join_field(self): return self._join_field
    @property
    def is_controller_filter(self): return self._is_controller_filter
    @property
    def allows_like(self): return self._allows_like
    @property
    def allows_between(self): return self._allows_between
    @property
    def sortable(self): return self._sortable
    @property
    def always_like(self): return self._always_like

    @classmethod
    def get_filter_by_json_field(cls, json_field):
        for f in cls:
            if f.json_field and f.json_field == json_field:
                return f
        return None
