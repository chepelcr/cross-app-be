"""Typed access helpers for the products.codes JSONB array.

The codes column stores a list of dicts shaped like ProductCodeResponse
(`code_type_id`, `number`, optional `description`). Anywhere we read from
that column we go through these helpers so the JSONB key shape lives in
one place — same `model_validate` discipline product_service uses for
taxes/discounts.
"""

from __future__ import annotations

from typing import Iterable, Optional

from pydantic import ValidationError

from app.dtos.responses.product_dto import ProductCodeResponse


def read_codes(raw: Optional[Iterable[dict]]) -> list[ProductCodeResponse]:
    """Validate a JSONB codes array into typed entries.

    Entries that fail validation (legacy / malformed data) are skipped so a
    single bad row doesn't break the whole order render. Use `find_code` or
    `find_code_number` for the common single-lookup case.
    """
    if not raw:
        return []
    out: list[ProductCodeResponse] = []
    for r in raw:
        try:
            out.append(ProductCodeResponse.model_validate(r))
        except ValidationError:
            continue
    return out


def find_code(
    raw: Optional[Iterable[dict]], code_type_id: str
) -> Optional[ProductCodeResponse]:
    """Return the first code matching the given Hacienda code type, or None."""
    for code in read_codes(raw):
        if code.code_type_id == code_type_id:
            return code
    return None


def find_code_number(raw: Optional[Iterable[dict]], code_type_id: str) -> str:
    """Return just the `number` field of the first matching code, or "" if none."""
    found = find_code(raw, code_type_id)
    return found.number if found else ""
