from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IdentificationRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Optional[int] = Field(None)
    code: Optional[str] = Field(None, max_length=10)
    number: Optional[str] = Field(None, min_length=9, max_length=50)


class PhoneRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    country_code: Optional[str] = Field(None, alias="countryCode", max_length=10)
    area_code: Optional[str] = Field(None, alias="areaCode", max_length=10)
    number: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=50)


class ResidenceRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state_id: Optional[int] = Field(None, alias="stateId", ge=0)
    county_id: Optional[int] = Field(None, alias="countyId", ge=0)
    district_id: Optional[int] = Field(None, alias="districtId", ge=0)
    address: Optional[str] = Field(None, max_length=500)


class ClientRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_name: Optional[str] = Field(None, alias="clientName")
    client_gln: Optional[str] = Field(None, alias="clientGln")
    identification: Optional[IdentificationRequestDTO] = Field(None)
    business_name: Optional[str] = Field(None, alias="businessName", max_length=255)
    nationality: Optional[str] = Field(None, min_length=2, max_length=3)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[PhoneRequestDTO] = Field(None)
    residence: Optional[ResidenceRequestDTO] = Field(None)

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.client_name and not self.client_gln:
            raise ValueError("At least one of client_name or client_gln is required")
        return self
