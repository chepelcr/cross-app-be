from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class IdentificationResponse(BaseModel):
    code: Optional[str] = Field(None)
    number: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class PhoneResponse(BaseModel):
    country_code: Optional[str] = Field(None)
    area_code: Optional[str] = Field(None)
    number: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ResidenceResponse(BaseModel):
    state_id: Optional[int] = Field(None)
    county_id: Optional[int] = Field(None)
    district_id: Optional[int] = Field(None)
    address: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ClientResponse(BaseModel):
    client_id: str = Field(...)
    company_id: str = Field(...)
    client_name: Optional[str] = Field(None)
    client_gln: Optional[str] = Field(None)
    status: int = Field(...)
    identification: Optional[IdentificationResponse] = Field(None)
    business_name: Optional[str] = Field(None)
    nationality: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[PhoneResponse] = Field(None)
    residence: Optional[ResidenceResponse] = Field(None)

    class Config:
        populate_by_name = True


class ClientListResponse(BaseModel):
    data: List[ClientResponse]
    pagination: PaginationResponse
