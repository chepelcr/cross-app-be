from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class DepartmentResponse(BaseModel):
    department_id: str = Field(..., alias="departmentId")
    company_id: str = Field(..., alias="companyId")
    client_id: str = Field(..., alias="clientId")
    department_code: str = Field(..., alias="departmentCode")
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None, alias="supplierCode")

    class Config:
        populate_by_name = True


class DepartmentListResponse(BaseModel):
    data: List[DepartmentResponse]
    pagination: PaginationResponse
