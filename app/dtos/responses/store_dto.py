from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class StoreResponse(BaseModel):
    store_id: str = Field(...)
    company_id: str = Field(...)
    client_id: str = Field(...)
    store_code: str = Field(...)
    store_name: Optional[str] = Field(None)
    slot_id: Optional[str] = Field(None)
    chain: Optional[str] = Field(None)
    gln: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class StoreListResponse(BaseModel):
    data: List[StoreResponse]
    pagination: PaginationResponse
