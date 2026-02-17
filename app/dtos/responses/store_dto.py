from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class StoreResponse(BaseModel):
    store_id: str = Field(..., alias="storeId")
    company_id: str = Field(..., alias="companyId")
    client_id: str = Field(..., alias="clientId")
    store_code: str = Field(..., alias="storeCode")
    store_name: Optional[str] = Field(None, alias="storeName")
    slot_id: Optional[str] = Field(None, alias="slotId")
    chain: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class StoreListResponse(BaseModel):
    data: List[StoreResponse]
    pagination: PaginationResponse
