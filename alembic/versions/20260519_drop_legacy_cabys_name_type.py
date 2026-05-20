"""drop legacy cabys.name and cabys.type columns

Revision ID: drop_legacy_cabys_name_type
Revises: add_customer_type_to_clients
Create Date: 2026-05-19

Context:
    The `cabys` table is shared with data-services, which owns the canonical
    schema (description, categories, status, country_code, product_type_id,
    tax_rate_id). cross-app-be previously added `name` and `type NOT NULL`
    columns and upserted into them during product save — that fought the
    data-services source-of-truth and left thousands of rows with NULL
    name/type (every row inserted by data-services search). The Pydantic
    CabysResponse on cross-app-be required name/type, producing 400s on
    product save for any product whose CABYS came in via the search path.

    Fix: drop the legacy columns. cross-app-be reads only the canonical
    fields going forward; FE sends `cabys_id` (UUID), no upsert needed.

    Live state at write time: 20,501 rows, all with name IS NULL and
    description populated — no data loss.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "drop_legacy_cabys_name_type"
down_revision: Union[str, None] = "add_customer_type_to_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("cabys", "name")
    op.drop_column("cabys", "type")


def downgrade() -> None:
    op.add_column("cabys", sa.Column("name", sa.Text(), nullable=True))
    op.add_column("cabys", sa.Column("type", sa.Integer(), nullable=True))
