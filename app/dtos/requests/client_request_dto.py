from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClientRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    client_name: Optional[str] = Field(None, alias="clientName")
    client_gln: Optional[str] = Field(None, alias="clientGln")

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.client_name and not self.client_gln:
            raise ValueError("At least one of client_name or client_gln is required")
        return self
