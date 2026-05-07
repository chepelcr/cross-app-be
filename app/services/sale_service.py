from __future__ import annotations

import logging
import uuid
from typing import Optional

from app.dtos.requests.create_sale_dto import CreateSaleDTO
from app.dtos.responses.pagination_dto import PaginationResponse
from app.dtos.responses.sale_response_dto import (
    SaleLineResponse,
    SaleListResponse,
    SalePaymentResponse,
    SaleResponse,
)
from app.models.sale import Sale
from app.models.sale_line import SaleLine
from app.repositories.branch_repository import BranchRepository
from app.repositories.sale_repository import SaleRepository
from app.repositories.terminal_repository import TerminalRepository

logger = logging.getLogger(__name__)


def create_sale(organization_id: str, user_id: str, dto: CreateSaleDTO) -> SaleResponse:
    """Register a new sale. Resolves branch/terminal from integer codes."""
    with BranchRepository() as b_repo:
        branch = b_repo.find_by_code_and_organization(dto.branch_code, organization_id)
        if not branch:
            raise ValueError(f"Branch with code {dto.branch_code} not found in this organization")

    with TerminalRepository() as t_repo:
        terminal = t_repo.find_by_code_and_branch(
            dto.terminal_code, str(branch.branch_id), organization_id
        )
        if not terminal:
            raise ValueError(
                f"Terminal with code {dto.terminal_code} not found in branch {dto.branch_code}"
            )

    client_id = uuid.UUID(dto.client_id) if dto.client_id else None

    receiver = dto.receiver
    sale = Sale(
        sale_id=uuid.uuid4(),
        organization_id=organization_id,
        assignment_id=dto.assignment_id,
        branch_code=dto.branch_code,
        terminal_code=dto.terminal_code,
        branch_id=branch.branch_id,
        terminal_id=terminal.terminal_id,
        client_id=client_id,
        document_type=dto.document_type,
        version_id=dto.version_id,
        activity_code=dto.activity_code,
        sale_condition_id=dto.sale_condition_id,
        credit_term=dto.credit_term,
        notes=dto.notes,
        copy_emails=dto.copy_emails,
        receiver_id_type=receiver.id_type if receiver else None,
        receiver_id_number=receiver.id_number if receiver else None,
        receiver_business_name=receiver.business_name if receiver else None,
        receiver_email=receiver.email if receiver else None,
        receiver_state_id=receiver.state_id if receiver else None,
        receiver_county_id=receiver.county_id if receiver else None,
        receiver_district_id=receiver.district_id if receiver else None,
        receiver_address=receiver.address if receiver else None,
        payments=[{"type": p.type, "amount": float(p.amount)} for p in dto.payments],
        subtotal=dto.subtotal,
        discount_amount=dto.discount_amount,
        tax_amount=dto.tax_amount,
        total_amount=dto.total_amount,
        created_by=user_id,
    )

    lines = [
        SaleLine(
            sale_id=sale.sale_id,
            line_number=i + 1,
            product_id=detail.product_id,
            description=detail.description,
            quantity=detail.quantity,
            unit_id=detail.unit_id,
            net_price=detail.net_price,
            discount_rate=detail.discount_rate,
            tax_rate=detail.tax_rate,
            line_total=round(
                detail.quantity * detail.net_price * (1 - detail.discount_rate / 100) * (1 + detail.tax_rate / 100),
                5,
            ),
        )
        for i, detail in enumerate(dto.details)
    ]

    with SaleRepository() as repo:
        sale = repo.save(sale)
        lines = repo.save_lines(lines)

    return _map_sale(sale, lines)


def get_sale(organization_id: str, user_id: str, sale_id: str) -> Optional[SaleResponse]:
    with SaleRepository() as repo:
        sale = repo.find_by_id_and_organization(sale_id, organization_id)
        if not sale:
            return None
        lines = repo.find_lines_by_sale(sale_id)
    return _map_sale(sale, lines)


def get_sales(
    organization_id: str,
    user_id: str,
    page: int = 1,
    page_size: int = 20,
) -> SaleListResponse:
    with SaleRepository() as repo:
        sales, total = repo.find_all_paginated(organization_id, page=page, page_size=page_size)

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return SaleListResponse(
        data=[_map_sale(s, []) for s in sales],
        pagination=PaginationResponse(
            page=page,
            page_size=page_size,
            total_elements=total,
            total_pages=total_pages,
        ),
    )


def _map_sale(sale: Sale, lines: list) -> SaleResponse:
    return SaleResponse(
        sale_id=str(sale.sale_id),
        organization_id=sale.organization_id,
        assignment_id=sale.assignment_id,
        branch_code=sale.branch_code,
        terminal_code=sale.terminal_code,
        branch_id=str(sale.branch_id),
        terminal_id=str(sale.terminal_id),
        client_id=str(sale.client_id) if sale.client_id else None,
        document_type=sale.document_type,
        version_id=sale.version_id,
        activity_code=sale.activity_code,
        sale_condition_id=sale.sale_condition_id,
        credit_term=sale.credit_term,
        notes=sale.notes,
        copy_emails=sale.copy_emails,
        receiver_id_type=sale.receiver_id_type,
        receiver_id_number=sale.receiver_id_number,
        receiver_business_name=sale.receiver_business_name,
        receiver_email=sale.receiver_email,
        payments=[SalePaymentResponse(type=p["type"], amount=p["amount"]) for p in (sale.payments or [])],
        subtotal=float(sale.subtotal),
        discount_amount=float(sale.discount_amount),
        tax_amount=float(sale.tax_amount),
        total_amount=float(sale.total_amount),
        lines=[
            SaleLineResponse(
                line_id=l.line_id,
                line_number=l.line_number,
                product_id=l.product_id,
                description=l.description,
                quantity=float(l.quantity),
                unit_id=l.unit_id,
                net_price=float(l.net_price),
                discount_rate=float(l.discount_rate),
                tax_rate=float(l.tax_rate),
                line_total=float(l.line_total),
            )
            for l in lines
        ],
        status=sale.status,
        created_at=sale.created_on.isoformat() if sale.created_on else None,
        created_by=sale.created_by,
    )
