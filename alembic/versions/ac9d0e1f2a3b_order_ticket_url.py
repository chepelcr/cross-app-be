"""order ticket_url — 80mm thermal ticket as a document format (TSR-127)

The ticket joins `pdf_url` / `excel_url` as another server-rendered format of
the order, rather than a browser print view. That is what makes a reprint
byte-identical to the original and lets one be emailed later.

Revision ID: ac9d0e1f2a3b
Revises: ab8c9d0e1f2a
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "ac9d0e1f2a3b"
down_revision: Union[str, None] = "ab8c9d0e1f2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "crossdocking_orders",
        sa.Column("ticket_url", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crossdocking_orders", "ticket_url")
