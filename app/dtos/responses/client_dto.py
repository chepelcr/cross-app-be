from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class IdentificationResponse(BaseModel):
    type: Optional[int] = Field(None)
    code: Optional[str] = Field(None)
    number: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class PhoneResponse(BaseModel):
    country_code: Optional[str] = Field(None, alias="countryCode")
    area_code: Optional[str] = Field(None, alias="areaCode")
    number: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ResidenceResponse(BaseModel):
    state_id: Optional[int] = Field(None, alias="stateId")
    county_id: Optional[int] = Field(None, alias="countyId")
    district_id: Optional[int] = Field(None, alias="districtId")
    address: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ClientResponse(BaseModel):
    client_id: str = Field(..., alias="clientId")
    company_id: str = Field(..., alias="companyId")
    client_name: Optional[str] = Field(None, alias="clientName")
    client_gln: Optional[str] = Field(None, alias="clientGln")
    status: int = Field(...)
    identification: Optional[IdentificationResponse] = Field(None)
    business_name: Optional[str] = Field(None, alias="businessName")
    nationality: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    phone: Optional[PhoneResponse] = Field(None)
    residence: Optional[ResidenceResponse] = Field(None)

    class Config:
        populate_by_name = True


class ClientListResponse(BaseModel):
    data: List[ClientResponse]
    pagination: PaginationResponse
