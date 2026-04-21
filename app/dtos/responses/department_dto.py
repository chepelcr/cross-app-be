from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class DepartmentDTO(BaseModel):
    """Lightweight department info embedded in order responses."""

    department_code: str = Field(...)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class DepartmentResponse(BaseModel):
    department_id: str = Field(...)
    company_id: str = Field(...)
    client_id: str = Field(...)
    department_code: str = Field(...)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class DepartmentListResponse(BaseModel):
    data: List[DepartmentResponse]
    pagination: PaginationResponse
