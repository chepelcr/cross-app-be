from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state_id: Optional[int] = Field(None)
    county_id: Optional[int] = Field(None)
    district_id: Optional[int] = Field(None)
    neighborhood_id: Optional[int] = Field(None)
    address: Optional[str] = Field(None)


class LocationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    state_id: Optional[int] = None
    county_id: Optional[int] = None
    district_id: Optional[int] = None
    neighborhood_id: Optional[int] = None
    address: Optional[str] = None
