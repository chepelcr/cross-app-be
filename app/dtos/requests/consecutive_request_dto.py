from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ConsecutiveCreateRequestDTO(BaseModel):
    terminal_id: str = Field(...)
    document_type_id: int = Field(...)
    initial_number: Optional[int] = Field(None, ge=0)
