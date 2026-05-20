"""canonicalize products.codes / discounts / taxes JSONB keys to snake_case

Revision ID: canon_prod_jsonb_keys
Revises: replace_unit_id_w_measure
Create Date: 2026-05-21

Context:
    Early product imports (Excel parser + initial seeds) wrote JSONB rows
    with camelCase keys: `codeTypeId`, `discountTypeId`, `taxTypeId`,
    `taxRate`, `taxFactor`, `specialFields`, `otherTaxType`, `isAmount`,
    `volumeConsumption`, `taxAmount`. The canonical shape is snake_case —
    that's what ProductCodeDTO / ProductTaxDTO / ProductDiscountDTO emit
    via model_dump() and what the validators + response models read with
    model_validate().

    Live state at write time: 39 products with camelCase codes, 0 with
    camelCase discounts/taxes, but we cover all three columns for
    idempotency and future-proofing.

    The transform recursively renames known camelCase keys to snake_case,
    leaves already-snake-case keys untouched, and is safe to re-run.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "canon_prod_jsonb_keys"
down_revision: Union[str, None] = "replace_unit_id_w_measure"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Top-level key renames per column.
_CODE_KEYS = {
    "codeTypeId": "code_type_id",
}
_DISCOUNT_KEYS = {
    "discountTypeId": "discount_type_id",
    "isAmount": "is_amount",
}
_TAX_KEYS = {
    "taxTypeId": "tax_type_id",
    "taxRate": "tax_rate",
    "taxFactor": "tax_factor",
    "otherTaxType": "other_tax_type",
    "specialFields": "special_fields",
    "isAmount": "is_amount",
}
_SPECIAL_FIELDS_KEYS = {
    "volumeConsumption": "volume_consumption",
    "taxAmount": "tax_amount",
}


def _rename_keys(d: dict, mapping: dict[str, str]) -> dict:
    """Return a new dict with mapped keys renamed; idempotent."""
    if not isinstance(d, dict):
        return d
    return {mapping.get(k, k): v for k, v in d.items()}


def _canon_code(entry: dict) -> dict:
    return _rename_keys(entry, _CODE_KEYS)


def _canon_discount(entry: dict) -> dict:
    return _rename_keys(entry, _DISCOUNT_KEYS)


def _canon_tax(entry: dict) -> dict:
    if not isinstance(entry, dict):
        return entry
    renamed = _rename_keys(entry, _TAX_KEYS)
    # Recurse into nested special_fields.tax_amount {id, amount} — keys
    # there are already snake_case (id, amount) and need no transform, but
    # the parent key `taxAmount` → `tax_amount` handled above.
    sf = renamed.get("special_fields")
    if isinstance(sf, dict):
        renamed["special_fields"] = _rename_keys(sf, _SPECIAL_FIELDS_KEYS)
    return renamed


def upgrade() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, codes, discounts, taxes FROM products "
            "WHERE codes IS NOT NULL OR discounts IS NOT NULL OR taxes IS NOT NULL"
        )
    ).fetchall()

    update_stmt = sa.text(
        "UPDATE products SET codes = :codes, discounts = :discounts, taxes = :taxes "
        "WHERE id = :id"
    )

    import json as _json
    touched = 0
    for row in rows:
        codes = [_canon_code(c) for c in (row.codes or [])]
        discounts = [_canon_discount(d) for d in (row.discounts or [])]
        taxes = [_canon_tax(t) for t in (row.taxes or [])]

        # Skip rows whose JSONB is already canonical to keep this idempotent.
        if codes == (row.codes or []) and discounts == (row.discounts or []) and taxes == (row.taxes or []):
            continue

        conn.execute(
            update_stmt,
            {
                "id": row.id,
                "codes": _json.dumps(codes),
                "discounts": _json.dumps(discounts),
                "taxes": _json.dumps(taxes),
            },
        )
        touched += 1

    print(f"canon_prod_jsonb_keys: rewrote {touched} row(s)")


def downgrade() -> None:
    # No reverse — once converted, callers expect snake_case throughout.
    pass
