from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class CategoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category_id: str = Field(...)
    organization_id: str = Field(...)
    name: str
    slug: str
    description: str
    background_color: str = Field(...)
    button_color: str = Field(...)
    image_1_url: Optional[str] = Field(None)
    image_2_url: Optional[str] = Field(None)
    is_active: bool = Field(...)
    sort_order: int = Field(...)


class CategoryListResponse(BaseModel):
    data: List[CategoryResponse]
    pagination: PaginationResponse
