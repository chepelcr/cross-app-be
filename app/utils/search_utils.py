from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional, Type

from sqlalchemy import and_, or_, asc, desc
from sqlalchemy.orm import InstrumentedAttribute

from app.enums.base_search_filter import BaseSearchFilter
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
    search_filter: Optional[BaseSearchFilter] = None
    filter_enum_class: Type[BaseSearchFilter] = None

    def __post_init__(self) -> None:
        # Use the provided filter enum class, or skip if not provided
        if self.filter_enum_class:
            search_filter = self.filter_enum_class.get_filter_by_json_field(self.field)
            if search_filter:
                self.search_filter = search_filter
                self.is_join_field = search_filter.is_join_field
                self.join_field = search_filter.join_field
                self.entity_field = search_filter.entity_field
            else:
                self.entity_field = self.field
        else:
            self.entity_field = self.field


class SearchUtils:
    _ORDER_BY_PATTERN = re.compile(r"orderBy([<>])([a-zA-Z_][a-zA-Z0-9_]*)")

    # Fields valid for orderBy (only direct columns, not join fields)
    SORTABLE_FIELDS = {
        "documentNumber", "document_number",
        "deliveryDate", "delivery_date",
        "creationDate", "creation_date",
        "orderStatus", "order_status",
        "createdOn", "created_on",
        "updatedOn", "updated_on",
    }

    SORTABLE_FIELD_MAP = {
        "documentNumber": "document_number",
        "deliveryDate": "delivery_date",
        "creationDate": "creation_date",
        "orderStatus": "order_status",
        "createdOn": "created_on",
        "updatedOn": "updated_on",
    }

    @classmethod
    def parse_search_filter(cls, search: str, entity_class: Type, filter_enum_class: Type[BaseSearchFilter] = None) -> tuple:
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
                order_result = cls._parse_order_by(token, entity_class, filter_enum_class)
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
                    criteria = cls._parse_criteria(gt, filter_enum_class)
                    if criteria:
                        f = cls._build_filter(criteria, entity_class)
                        if f is not None:
                            or_filters.append(f)
                if or_filters:
                    grouped_filters.append(or_(*or_filters) if len(or_filters) > 1 else or_filters[0])
            else:
                criteria = cls._parse_criteria(token, filter_enum_class)
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
    def _parse_criteria(cls, token: str, filter_enum_class: Type[BaseSearchFilter] = None) -> Optional[SearchCriteria]:
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
                            if filter_enum_class:
                                search_filter = filter_enum_class.get_filter_by_json_field(field)
                                if search_filter and search_filter.allows_between:
                                    if operation == SearchOperations.NEGATION:
                                        operation = SearchOperations.NEGATION_BETWEEN
                                    else:
                                        operation = SearchOperations.BETWEEN
                                    return SearchCriteria(
                                        field=field,
                                        operation=operation,
                                        value=value,
                                        filter_enum_class=filter_enum_class,
                                    )

                        operation, value = cls._process_wildcard_value(operation, value)
                        converted_value = cls._convert_value(value)
                        return SearchCriteria(
                            field=field,
                            operation=operation,
                            value=converted_value,
                            filter_enum_class=filter_enum_class,
                        )
        return None

    @classmethod
    def _process_wildcard_value(cls, operation: SearchOperations, value: str) -> tuple:
        if ZERO_OR_MORE_REGEX not in value:
            return operation, value

        # Value contains wildcards - convert to LIKE pattern
        starts_with_wildcard = value.startswith(ZERO_OR_MORE_REGEX)
        ends_with_wildcard = value.endswith(ZERO_OR_MORE_REGEX)

        # Replace wildcards with SQL LIKE wildcards
        processed_value = value.replace(ZERO_OR_MORE_REGEX, "%")

        if starts_with_wildcard and ends_with_wildcard:
            return SearchOperations.CONTAINS, processed_value
        elif starts_with_wildcard:
            return SearchOperations.ENDS_WITH, processed_value
        elif ends_with_wildcard:
            return SearchOperations.STARTS_WITH, processed_value

        # Middle wildcards - use CONTAINS
        return SearchOperations.CONTAINS, processed_value

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
        if criteria.is_join_field and criteria.join_field:
            # Handle nested joins (e.g., "terminal.branch")
            join_parts = criteria.join_field.split(".")
            current_class = entity_class

            for join_name in join_parts:
                if not hasattr(current_class, join_name):
                    return None
                relationship_attr = getattr(current_class, join_name)
                # Get the related class from the relationship
                try:
                    # Try newer SQLAlchemy API first
                    if hasattr(relationship_attr.property, 'entity'):
                        current_class = relationship_attr.property.entity.class_
                    elif hasattr(relationship_attr.property, 'mapper'):
                        current_class = relationship_attr.property.mapper.class_
                    else:
                        # Fallback: try to get from the relationship itself
                        current_class = relationship_attr.property.argument
                        if callable(current_class):
                            current_class = current_class()
                except AttributeError:
                    return None

            # current_class is now the final related class after all joins
            related_class = current_class

            # Get the field from the related class
            field_name = criteria.entity_field or criteria.field
            if not hasattr(related_class, field_name):
                return None

            target_column = getattr(related_class, field_name)
            return cls._apply_operation(target_column, criteria.operation, criteria.value, criteria.field, criteria.search_filter)

        field_name = criteria.entity_field or criteria.field
        
        # Special handling for JSONB codes field in Product
        if field_name == "codes" and criteria.field == "code":
            return cls._build_codes_filter(entity_class, criteria.operation, criteria.value)
        
        if not hasattr(entity_class, field_name):
            return None
        column: InstrumentedAttribute = getattr(entity_class, field_name)
        return cls._apply_operation(column, criteria.operation, criteria.value, criteria.field, criteria.search_filter)

    @classmethod
    def _build_codes_filter(cls, entity_class: Type, operation: SearchOperations, value: Any):
        """Build filter for JSONB codes array with format: code:01-123415 or code:123415"""
        from sqlalchemy import cast, String, func
        from sqlalchemy.dialects.postgresql import JSONB
        
        if not hasattr(entity_class, "codes"):
            return None
        
        codes_column = getattr(entity_class, "codes")
        value_str = str(value)
        
        # Check if value contains code type (format: 01-123415)
        if "-" in value_str:
            parts = value_str.split("-", 1)
            code_type = parts[0].strip()
            code_number = parts[1].strip()
            
            # Search for exact match with both codeTypeId and number
            # JSONB query: codes @> '[{"codeTypeId": "01", "number": "123415"}]'
            search_obj = [{"codeTypeId": code_type, "number": code_number}]
            if operation == SearchOperations.EQUALITY:
                return codes_column.op("@>")(cast(search_obj, JSONB))
            elif operation == SearchOperations.NEGATION:
                return ~codes_column.op("@>")(cast(search_obj, JSONB))
        else:
            # No code type specified, search all code types for the number
            # Use jsonb_array_elements to expand array and check number field
            if operation == SearchOperations.EQUALITY:
                return codes_column.op("@>")(cast([{"number": value_str}], JSONB))
            elif operation == SearchOperations.NEGATION:
                return ~codes_column.op("@>")(cast([{"number": value_str}], JSONB))
        
        return None

    @classmethod
    def _apply_operation(cls, column, operation: SearchOperations, value: Any, field_name: Optional[str] = None, search_filter = None):
        # Handle type conversions based on column type
        try:
            col_type = str(column.type)
            
            # Handle VARCHAR/TEXT columns - ensure value is string
            if "VARCHAR" in col_type.upper() or "TEXT" in col_type.upper() or "CHAR" in col_type.upper():
                if value is not None and operation not in (SearchOperations.BETWEEN, SearchOperations.NEGATION_BETWEEN):
                    value = str(value)
            
            # Handle INTEGER columns - ensure value is integer (no boolean conversion for status)
            elif "INTEGER" in col_type.upper():
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                elif isinstance(value, bool):
                    # Convert boolean to integer for backward compatibility
                    value = 1 if value else 2
        except Exception:
            pass

        # Check if field has always_like property set to True
        always_like = False
        if search_filter and hasattr(search_filter, 'always_like'):
            always_like = search_filter.always_like

        # For always_like fields, convert EQUALITY to case-insensitive LIKE
        if operation == SearchOperations.EQUALITY and always_like:
            return column.ilike(f"%{value}%")

        if operation == SearchOperations.NEGATION and always_like:
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
            # Value already has % from wildcard processing
            if isinstance(value, str) and "%" in value:
                return column.ilike(value)
            return column.ilike(f"{value}%")
        elif operation == SearchOperations.ENDS_WITH:
            # Value already has % from wildcard processing
            if isinstance(value, str) and "%" in value:
                return column.ilike(value)
            return column.ilike(f"%{value}")
        elif operation == SearchOperations.CONTAINS:
            # Value already has % from wildcard processing
            if isinstance(value, str) and "%" in value:
                return column.ilike(value)
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
    def _parse_order_by(cls, token: str, entity_class: Type, filter_enum_class: Type[BaseSearchFilter] = None):
        match = cls._ORDER_BY_PATTERN.match(token)
        if not match:
            return None

        direction_char = match.group(1)
        field_name = match.group(2)

        # Check if field exists in the filter enum
        if filter_enum_class:
            search_filter = filter_enum_class.get_filter_by_json_field(field_name)
            
            # If in filter enum, check if it's sortable
            if search_filter:
                if not hasattr(search_filter, 'sortable') or not search_filter.sortable:
                    raise ValueError(f"Cannot sort by field: {field_name}")
                entity_field_name = search_filter.entity_field
            # Otherwise check global sortable fields (for backward compatibility)
            elif field_name in cls.SORTABLE_FIELDS:
                entity_field_name = cls.SORTABLE_FIELD_MAP.get(field_name, field_name)
            else:
                raise ValueError(f"Cannot sort by field: {field_name}")
        else:
            # No filter enum provided, use global sortable fields
            if field_name in cls.SORTABLE_FIELDS:
                entity_field_name = cls.SORTABLE_FIELD_MAP.get(field_name, field_name)
            else:
                raise ValueError(f"Cannot sort by field: {field_name}")

        # Check if the entity has this field
        if not hasattr(entity_class, entity_field_name):
            raise ValueError(f"Cannot sort by field: {field_name} (entity field: {entity_field_name} not found)")

        column = getattr(entity_class, entity_field_name)
        if direction_char == ">":
            return asc(column), "ASC"
        else:
            return desc(column), "DESC"
