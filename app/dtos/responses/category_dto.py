from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class CategoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category_id: str = Field(alias="categoryId")
    organization_id: str = Field(alias="organizationId")
    name: str
    slug: str
    description: str
    background_color: str = Field(alias="backgroundColor")
    button_color: str = Field(alias="buttonColor")
    image_1_url: Optional[str] = Field(None, alias="image1Url")
    image_2_url: Optional[str] = Field(None, alias="image2Url")
    is_active: bool = Field(alias="isActive")
    sort_order: int = Field(alias="sortOrder")


class CategoryListResponse(BaseModel):
    data: List[CategoryResponse]
    pagination: PaginationResponse
