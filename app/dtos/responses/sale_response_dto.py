from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.dtos.responses.pagination_dto import PaginationResponse


class SaleLineResponse(BaseModel):
    line_id: int
    line_number: int
    product_id: Optional[str] = None
    description: str
    quantity: float
    unit_id: Optional[int] = None
    net_price: float
    discount_rate: float
    tax_rate: float
    line_total: float

    model_config = {"from_attributes": True}


class SalePaymentResponse(BaseModel):
    type: int
    amount: float


class SaleResponse(BaseModel):
    sale_id: str
    organization_id: str
    assignment_id: Optional[str] = None
    branch_code: int
    terminal_code: int
    branch_id: str
    terminal_id: str
    client_id: Optional[str] = None

    document_type: int
    version_id: int
    activity_code: str
    sale_condition_id: int
    credit_term: str
    notes: Optional[str] = None
    copy_emails: Optional[List[str]] = None

    receiver_id_type: Optional[int] = None
    receiver_id_number: Optional[str] = None
    receiver_business_name: Optional[str] = None
    receiver_email: Optional[str] = None

    payments: List[SalePaymentResponse]
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float

    lines: List[SaleLineResponse] = []
    status: int
    created_at: Optional[str] = None
    created_by: str

    model_config = {"from_attributes": True}


class SaleListResponse(BaseModel):
    data: List[SaleResponse]
    pagination: PaginationResponse
