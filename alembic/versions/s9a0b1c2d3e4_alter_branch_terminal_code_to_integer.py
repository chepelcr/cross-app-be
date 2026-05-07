"""alter branch and terminal code to integer

Revision ID: s9a0b1c2d3e4
Revises: 20260506000000
Create Date: 2026-05-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 's9a0b1c2d3e4'
down_revision: Union[str, Sequence[str], None] = '20260506000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Branches: rows whose code is already a valid integer keep their value;
    # non-numeric codes are reassigned a sequential integer per organization.
    op.execute(sa.text("""
        WITH ranked AS (
            SELECT branch_id,
                   ROW_NUMBER() OVER (PARTITION BY organization_id ORDER BY created_on) AS new_code
            FROM branches
            WHERE code !~ '^[0-9]+$'
        )
        UPDATE branches b
        SET code = r.new_code::text
        FROM ranked r
        WHERE b.branch_id = r.branch_id
    """))
    op.execute(sa.text(
        "ALTER TABLE branches ALTER COLUMN code TYPE INTEGER USING code::integer"
    ))

    # Terminals: same approach — non-numeric codes get sequential integers per branch.
    op.execute(sa.text("""
        WITH ranked AS (
            SELECT terminal_id,
                   ROW_NUMBER() OVER (PARTITION BY branch_id ORDER BY created_on) AS new_code
            FROM terminals
            WHERE code !~ '^[0-9]+$'
        )
        UPDATE terminals t
        SET code = r.new_code::text
        FROM ranked r
        WHERE t.terminal_id = r.terminal_id
    """))
    op.execute(sa.text(
        "ALTER TABLE terminals ALTER COLUMN code TYPE INTEGER USING code::integer"
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "ALTER TABLE branches ALTER COLUMN code TYPE VARCHAR(50) USING code::varchar"
    ))
    op.execute(sa.text(
        "ALTER TABLE terminals ALTER COLUMN code TYPE VARCHAR(50) USING code::varchar"
    ))
