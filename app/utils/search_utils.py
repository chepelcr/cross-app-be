from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional, Type

from sqlalchemy import and_, or_, asc, desc
from sqlalchemy.orm import InstrumentedAttribute

from app.enums.search_filters import SearchFilters
from app.enums.search_operations import (
    SearchOperations,
    SIMPLE_OPERATION_SET,
    ZERO_OR_MORE_REGEX,
    BETWEEN_RANGE_SEPARATOR,
    LEFT_PARENTHESIS,
    RIGHT_PARENTHESIS,
)


@dataclass
class SearchCriteria:
    field: str
    operation: SearchOperations
    value: Any
    is_join_field: bool = False
    join_field: Optional[str] = None
    entity_field: Optional[str] = None
    search_filter: Optional[SearchFilters] = None

    def __post_init__(self) -> None:
        search_filter = SearchFilters.get_filter_by_json_field(self.field)
        if search_filter:
            self.search_filter = search_filter
            self.is_join_field = search_filter.is_join_field
            self.join_field = search_filter.join_field
            self.entity_field = search_filter.entity_field
        else:
            self.entity_field = self.field


class SearchUtils:
    _ORDER_BY_PATTERN = re.compile(r"orderBy([<>])([a-zA-Z_][a-zA-Z0-9_]*)")

    # Text fields that always use case-insensitive LIKE
    ALWAYS_LIKE_FIELDS = {"documentNumber", "clientName", "supplierName", "deliverToName", "confirmationNumber"}

    # Fields valid for orderBy
    SORTABLE_FIELDS = {
        "documentNumber", "document_number",
        "clientName", "client_name",
        "supplierName", "supplier_name",
        "deliveryDate", "delivery_date",
        "creationDate", "creation_date",
        "orderStatus", "order_status",
        "createdOn", "created_on",
        "updatedOn", "updated_on",
    }

    SORTABLE_FIELD_MAP = {
        "documentNumber": "document_number",
        "clientName": "client_name",
        "supplierName": "supplier_name",
        "deliveryDate": "delivery_date",
        "creationDate": "creation_date",
        "orderStatus": "order_status",
        "createdOn": "created_on",
        "updatedOn": "updated_on",
    }

    @classmethod
    def parse_search_filter(cls, search: str, entity_class: Type) -> tuple:
        if not search or not search.strip():
            return [], None

        order_by = None
        tokens = cls._split_tokens(search)

        general_filters = []
        grouped_filters = []

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            if token.startswith("orderBy"):
                order_result = cls._parse_order_by(token, entity_class)
                if order_result:
                    order_by = order_result
                continue

            if token.startswith(LEFT_PARENTHESIS) and token.endswith(RIGHT_PARENTHESIS):
                group_content = token[1:-1]
                group_tokens = cls._split_tokens(group_content)
                or_filters = []
                for gt in group_tokens:
                    gt = gt.strip()
                    if not gt:
                        continue
                    criteria = cls._parse_criteria(gt)
                    if criteria:
                        f = cls._build_filter(criteria, entity_class)
                        if f is not None:
                            or_filters.append(f)
                if or_filters:
                    grouped_filters.append(or_(*or_filters) if len(or_filters) > 1 else or_filters[0])
            else:
                criteria = cls._parse_criteria(token)
                if criteria:
                    f = cls._build_filter(criteria, entity_class)
                    if f is not None:
                        general_filters.append(f)

        all_filters = general_filters + grouped_filters
        if all_filters:
            if len(all_filters) == 1:
                return [all_filters[0]], order_by
            return [and_(*all_filters)], order_by

        return [], order_by

    @classmethod
    def _split_tokens(cls, search_string: str) -> list[str]:
        tokens = []
        current_token = ""
        paren_depth = 0

        for char in search_string:
            if char == LEFT_PARENTHESIS:
                paren_depth += 1
                current_token += char
            elif char == RIGHT_PARENTHESIS:
                paren_depth -= 1
                current_token += char
            elif char == "," and paren_depth == 0:
                if current_token.strip():
                    tokens.append(current_token.strip())
                current_token = ""
            else:
                current_token += char

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    @classmethod
    def _parse_criteria(cls, token: str) -> Optional[SearchCriteria]:
        if not token:
            return None

        for op_char in SIMPLE_OPERATION_SET:
            if op_char in token:
                parts = token.split(op_char, 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip()
                    operation = SearchOperations.get_simple_operation(op_char)
                    if operation:
                        # Check for BETWEEN range separator in value
                        if BETWEEN_RANGE_SEPARATOR in value:
                            search_filter = SearchFilters.get_filter_by_json_field(field)
                            if search_filter and search_filter.allows_between:
                                if operation == SearchOperations.NEGATION:
                                    operation = SearchOperations.NEGATION_BETWEEN
                                else:
                                    operation = SearchOperations.BETWEEN
                                return SearchCriteria(
                                    field=field,
                                    operation=operation,
                                    value=value,
                                )

                        operation, value = cls._process_wildcard_value(operation, value)
                        converted_value = cls._convert_value(value)
                        return SearchCriteria(
                            field=field,
                            operation=operation,
                            value=converted_value,
                        )
        return None

    @classmethod
    def _process_wildcard_value(cls, operation: SearchOperations, value: str) -> tuple:
        if ZERO_OR_MORE_REGEX not in value:
            return operation, value
        if operation != SearchOperations.EQUALITY:
            return operation, value

        starts = value.startswith(ZERO_OR_MORE_REGEX)
        ends = value.endswith(ZERO_OR_MORE_REGEX)
        processed = value.strip(ZERO_OR_MORE_REGEX)

        if starts and ends:
            return SearchOperations.CONTAINS, processed
        elif starts:
            return SearchOperations.ENDS_WITH, processed
        elif ends:
            return SearchOperations.STARTS_WITH, processed

        return SearchOperations.CONTAINS, processed

    @classmethod
    def _convert_value(cls, value: str) -> Any:
        if not value:
            return value
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @classmethod
    def _build_filter(cls, criteria: SearchCriteria, entity_class: Type):
        field_name = criteria.entity_field or criteria.field
        if not hasattr(entity_class, field_name):
            return None
        column: InstrumentedAttribute = getattr(entity_class, field_name)
        return cls._apply_operation(column, criteria.operation, criteria.value, criteria.field)

    @classmethod
    def _apply_operation(cls, column, operation: SearchOperations, value: Any, field_name: Optional[str] = None):
        # Ensure string comparison for VARCHAR columns
        try:
            col_type = str(column.type)
            if "VARCHAR" in col_type.upper() or "TEXT" in col_type.upper() or "CHAR" in col_type.upper():
                if value is not None and operation not in (SearchOperations.BETWEEN, SearchOperations.NEGATION_BETWEEN):
                    value = str(value)
        except Exception:
            pass

        # For ALWAYS_LIKE_FIELDS, convert EQUALITY to case-insensitive LIKE
        if operation == SearchOperations.EQUALITY and field_name in cls.ALWAYS_LIKE_FIELDS:
            return column.ilike(f"%{value}%")

        if operation == SearchOperations.NEGATION and field_name in cls.ALWAYS_LIKE_FIELDS:
            return ~column.ilike(f"%{value}%")

        if operation == SearchOperations.EQUALITY:
            return column == value
        elif operation == SearchOperations.NEGATION:
            return column != value
        elif operation == SearchOperations.GREATER_THAN:
            return column > value
        elif operation == SearchOperations.LESS_THAN:
            return column < value
        elif operation == SearchOperations.LIKE:
            return column.ilike(f"%{value}%")
        elif operation == SearchOperations.STARTS_WITH:
            return column.ilike(f"{value}%")
        elif operation == SearchOperations.ENDS_WITH:
            return column.ilike(f"%{value}")
        elif operation == SearchOperations.CONTAINS:
            return column.ilike(f"%{value}%")
        elif operation == SearchOperations.BETWEEN:
            if isinstance(value, str) and BETWEEN_RANGE_SEPARATOR in value:
                parts = value.split(BETWEEN_RANGE_SEPARATOR)
                if len(parts) == 2:
                    min_val = parts[0].strip()
                    max_val = parts[1].strip()
                    return and_(column >= min_val, column <= max_val)
            return column == value
        elif operation == SearchOperations.NEGATION_BETWEEN:
            if isinstance(value, str) and BETWEEN_RANGE_SEPARATOR in value:
                parts = value.split(BETWEEN_RANGE_SEPARATOR)
                if len(parts) == 2:
                    min_val = parts[0].strip()
                    max_val = parts[1].strip()
                    return or_(column < min_val, column > max_val)
            return column != value
        else:
            return column == value

    @classmethod
    def _parse_order_by(cls, token: str, entity_class: Type):
        match = cls._ORDER_BY_PATTERN.match(token)
        if not match:
            return None

        direction_char = match.group(1)
        field_name = match.group(2)

        if field_name not in cls.SORTABLE_FIELDS:
            raise ValueError(f"Cannot sort by field: {field_name}")

        search_filter = SearchFilters.get_filter_by_json_field(field_name)
        if field_name in cls.SORTABLE_FIELD_MAP:
            mapped = cls.SORTABLE_FIELD_MAP[field_name]
        else:
            mapped = field_name

        entity_field_name = search_filter.entity_field if search_filter and search_filter.entity_field else mapped

        if not hasattr(entity_class, entity_field_name):
            return None

        column = getattr(entity_class, entity_field_name)
        if direction_char == ">":
            return asc(column), "ASC"
        else:
            return desc(column), "DESC"
