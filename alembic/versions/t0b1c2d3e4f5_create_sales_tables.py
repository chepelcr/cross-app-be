"""create sales and sale_lines tables

Revision ID: t0b1c2d3e4f5
Revises: s9a0b1c2d3e4
Create Date: 2026-05-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID


revision: str = 't0b1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 's9a0b1c2d3e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'sales',
        sa.Column('sale_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('organization_id', sa.String(255), nullable=False),
        sa.Column('assignment_id', sa.String(255), nullable=True),
        sa.Column('branch_code', sa.Integer(), nullable=False),
        sa.Column('terminal_code', sa.Integer(), nullable=False),
        sa.Column('branch_id', UUID(as_uuid=True), sa.ForeignKey('branches.branch_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('terminal_id', UUID(as_uuid=True), sa.ForeignKey('terminals.terminal_id', ondelete='RESTRICT'), nullable=False),
        sa.Column('client_id', UUID(as_uuid=True), sa.ForeignKey('clients.client_id', ondelete='SET NULL'), nullable=True),
        sa.Column('document_type', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('activity_code', sa.String(20), nullable=False),
        sa.Column('sale_condition_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('credit_term', sa.String(10), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('copy_emails', JSON, nullable=True),
        sa.Column('receiver_id_type', sa.Integer(), nullable=True),
        sa.Column('receiver_id_number', sa.String(50), nullable=True),
        sa.Column('receiver_business_name', sa.String(255), nullable=True),
        sa.Column('receiver_email', sa.String(255), nullable=True),
        sa.Column('receiver_state_id', sa.Integer(), nullable=True),
        sa.Column('receiver_county_id', sa.Integer(), nullable=True),
        sa.Column('receiver_district_id', sa.Integer(), nullable=True),
        sa.Column('receiver_address', sa.Text(), nullable=True),
        sa.Column('payments', JSON, nullable=False, server_default='[]'),
        sa.Column('subtotal', sa.Numeric(18, 5), nullable=False),
        sa.Column('discount_amount', sa.Numeric(18, 5), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(18, 5), nullable=False, server_default='0'),
        sa.Column('total_amount', sa.Numeric(18, 5), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_on', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.Column('deleted_on', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_sales_org', 'sales', ['organization_id'])
    op.create_index('idx_sales_org_branch', 'sales', ['organization_id', 'branch_code'])
    op.create_index('idx_sales_org_created', 'sales', ['organization_id', 'created_on'])
    op.create_index('idx_sales_assignment', 'sales', ['assignment_id'])

    op.create_table(
        'sale_lines',
        sa.Column('line_id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('sale_id', UUID(as_uuid=True), sa.ForeignKey('sales.sale_id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(255), nullable=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 5), nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=True),
        sa.Column('net_price', sa.Numeric(18, 5), nullable=False),
        sa.Column('discount_rate', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False, server_default='13'),
        sa.Column('line_total', sa.Numeric(18, 5), nullable=False),
        sa.Column('created_on', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.Column('deleted_on', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_sale_lines_sale_id', 'sale_lines', ['sale_id'])


def downgrade() -> None:
    op.drop_index('idx_sale_lines_sale_id', table_name='sale_lines')
    op.drop_table('sale_lines')
    op.drop_index('idx_sales_assignment', table_name='sales')
    op.drop_index('idx_sales_org_created', table_name='sales')
    op.drop_index('idx_sales_org_branch', table_name='sales')
    op.drop_index('idx_sales_org', table_name='sales')
    op.drop_table('sales')
