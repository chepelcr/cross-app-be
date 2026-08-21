"""create branch_types table (per-org branch type catalog)

Replaces the hardcoded `stand`/`restaurant` enum with an org-configurable catalog:

* creates `branch_types`,
* drops the `check_branch_type` CHECK constraint that pinned `branches.type` to
  `('stand','restaurant')` — with the catalog in place the allowed values are data,
  not schema,
* seeds each organization's catalog from the type codes its branches already use,
  always including the two legacy defaults, so nothing that exists today stops
  resolving to a catalog entry.

Revision ID: z6b7c8d9e0f1
Revises: y5a6b7c8d9e0
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z6b7c8d9e0f1'
down_revision: Union[str, Sequence[str], None] = 'y5a6b7c8d9e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the catalog table, free `branches.type`, and seed existing orgs."""
    op.create_table(
        'branch_types',
        sa.Column('branch_type_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=50), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=True, server_default=sa.text('now()')),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.Column('deleted_on', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('branch_type_id'),
    )
    op.create_index('idx_branch_types_org', 'branch_types', ['organization_id'])
    op.create_index('idx_branch_types_status', 'branch_types', ['organization_id', 'status'])
    op.create_index(
        'idx_branch_types_org_code', 'branch_types', ['organization_id', 'code'], unique=True
    )

    # The catalog is now the source of truth for allowed values.
    op.execute(sa.text('ALTER TABLE branches DROP CONSTRAINT IF EXISTS check_branch_type'))

    # Seed: every code each org's branches already use, plus the legacy defaults, so
    # existing branches keep resolving and orgs start from a usable catalog.
    op.execute(sa.text("""
        INSERT INTO branch_types (
            branch_type_id, organization_id, code, name, icon, color,
            sort_order, status, created_by, created_on
        )
        SELECT
            gen_random_uuid(),
            seed.organization_id,
            seed.code,
            CASE seed.code
                WHEN 'stand' THEN 'Puesto'
                WHEN 'restaurant' THEN 'Restaurante'
                ELSE initcap(replace(seed.code, '_', ' '))
            END,
            CASE seed.code
                WHEN 'restaurant' THEN 'home'
                ELSE 'store'
            END,
            CASE seed.code
                WHEN 'restaurant' THEN 'info'
                ELSE 'primary'
            END,
            CASE seed.code
                WHEN 'stand' THEN 0
                WHEN 'restaurant' THEN 1
                ELSE 2
            END,
            1,
            'system',
            NOW()
        FROM (
            SELECT DISTINCT organization_id, type AS code
            FROM branches
            WHERE type IS NOT NULL AND type <> ''
            UNION
            SELECT DISTINCT b.organization_id, d.code
            FROM branches b
            CROSS JOIN (VALUES ('stand'), ('restaurant')) AS d(code)
        ) AS seed
        ON CONFLICT DO NOTHING
    """))


def downgrade() -> None:
    """Drop the catalog and restore the legacy CHECK constraint."""
    op.drop_index('idx_branch_types_org_code', table_name='branch_types')
    op.drop_index('idx_branch_types_status', table_name='branch_types')
    op.drop_index('idx_branch_types_org', table_name='branch_types')
    op.drop_table('branch_types')

    # Only re-add the constraint if every existing row would satisfy it — otherwise
    # the downgrade would fail on data the catalog legitimately allowed.
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM branches WHERE type NOT IN ('stand', 'restaurant')
            ) THEN
                ALTER TABLE branches
                    ADD CONSTRAINT check_branch_type CHECK (type IN ('stand', 'restaurant'));
            END IF;
        END $$;
    """))
