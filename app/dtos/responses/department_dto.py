from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class DepartmentDTO(BaseModel):
    """Lightweight department info embedded in order responses."""
    
    model_config = {"from_attributes": True}

    department_code: str = Field(...)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)


class DepartmentResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    department_id: str = Field(...)
    company_id: str = Field(...)
    client_id: str = Field(...)
    department_code: str = Field(...)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)


class DepartmentListResponse(BaseModel):
    data: List[DepartmentResponse]
    pagination: PaginationResponse
