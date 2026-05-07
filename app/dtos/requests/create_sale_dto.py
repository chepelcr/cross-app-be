from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SaleReceiverDTO(BaseModel):
    id_type: Optional[int] = None
    id_number: Optional[str] = Field(None, max_length=50)
    business_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    state_id: Optional[int] = None
    county_id: Optional[int] = None
    district_id: Optional[int] = None
    address: Optional[str] = None


class SaleLineDTO(BaseModel):
    product_id: Optional[str] = Field(None, max_length=255)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(..., gt=0)
    unit_id: Optional[int] = None
    net_price: float = Field(..., ge=0)
    discount_rate: float = Field(default=0, ge=0, le=100)
    tax_rate: float = Field(default=13, ge=0, le=100)


class SalePaymentDTO(BaseModel):
    type: int = Field(..., ge=1, description="Payment type code (1=Cash, 2=Check, 3=Card, 4=SINPE, 99=Other)")
    amount: float = Field(..., gt=0)


class CreateSaleDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    assignment_id: Optional[str] = Field(None, max_length=255)
    branch_code: int = Field(..., ge=1, description="Integer branch code, unique per org")
    terminal_code: int = Field(..., ge=1, description="Integer terminal code, unique per org")
    client_id: Optional[str] = Field(None, description="UUID of the client (optional)")

    # Hacienda document fields
    document_type: int = Field(default=1)
    version_id: int = Field(default=1)
    activity_code: str = Field(..., max_length=20)
    sale_condition_id: int = Field(default=1)
    credit_term: str = Field(default="0", max_length=10)
    notes: Optional[str] = None
    copy_emails: Optional[List[str]] = None

    receiver: Optional[SaleReceiverDTO] = None
    details: List[SaleLineDTO] = Field(..., min_length=1)
    payments: List[SalePaymentDTO] = Field(..., min_length=1)

    subtotal: float = Field(..., ge=0)
    discount_amount: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total_amount: float = Field(..., ge=0)
