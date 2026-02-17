from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StoreRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    store_code: Optional[str] = Field(None, alias="storeCode")
    store_name: Optional[str] = Field(None, alias="storeName")
    slot_id: Optional[str] = Field(None, alias="slotId")
    chain: Optional[str] = Field(None)
