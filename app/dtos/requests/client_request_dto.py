from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClientRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_name: Optional[str] = Field(None, alias="clientName")
    client_gln: Optional[str] = Field(None, alias="clientGln")
