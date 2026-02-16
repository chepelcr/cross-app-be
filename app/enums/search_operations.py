from __future__ import annotations

from enum import Enum
from typing import Optional


class SearchOperations(Enum):
    EQUALITY = ":"
    NEGATION = "!"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    LIKE = "~"
    STARTS_WITH = "^sw"
    ENDS_WITH = "$"
    CONTAINS = "*"
    BETWEEN = "^"
    NEGATION_BETWEEN = "!^"

    @classmethod
    def get_simple_operation(cls, input_char: str) -> Optional[SearchOperations]:
        operation_map = {
            ":": cls.EQUALITY,
            "!": cls.NEGATION,
            ">": cls.GREATER_THAN,
            "<": cls.LESS_THAN,
            "~": cls.LIKE,
        }
        return operation_map.get(input_char)


SIMPLE_OPERATION_SET: list[str] = [":", "!", ">", "<", "~"]
ZERO_OR_MORE_REGEX: str = "*"
BETWEEN_RANGE_SEPARATOR: str = "~"
LEFT_PARENTHESIS: str = "("
RIGHT_PARENTHESIS: str = ")"
