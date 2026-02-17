from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class ClientResponse(BaseModel):
    client_id: str = Field(..., alias="clientId")
    company_id: str = Field(..., alias="companyId")
    client_name: Optional[str] = Field(None, alias="clientName")
    client_gln: Optional[str] = Field(None, alias="clientGln")

    class Config:
        populate_by_name = True


class ClientListResponse(BaseModel):
    data: List[ClientResponse]
    pagination: PaginationResponse
