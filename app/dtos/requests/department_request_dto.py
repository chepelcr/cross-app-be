from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateDepartmentDTO(BaseModel):
    department_code: str = Field(...)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class UpdateDepartmentDTO(BaseModel):
    department_code: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    supplier_code: Optional[str] = Field(None)

    class Config:
        populate_by_name = True
