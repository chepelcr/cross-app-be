from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.dtos.responses.pagination_dto import PaginationResponse


class CategoryResponse(BaseModel):
    category_id: str = Field(..., alias="categoryId")
    name: Optional[str] = Field(None)

    class Config:
        populate_by_name = True


class ProductResponse(BaseModel):
    product_id: str = Field(..., alias="productId")
    company_id: str = Field(..., alias="companyId")
    internal_code: Optional[str] = Field(None, alias="internalCode")
    original_code: Optional[str] = Field(None, alias="originalCode")
    client_article_code: Optional[str] = Field(None, alias="clientArticleCode")
    code: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    units_per_box: Optional[int] = Field(None, alias="unitsPerBox")
    price: Optional[float] = Field(None)
    image_url: Optional[str] = Field(None, alias="imageUrl")
    category: Optional[CategoryResponse] = Field(None)

    class Config:
        populate_by_name = True


class ProductListResponse(BaseModel):
    data: List[ProductResponse]
    pagination: PaginationResponse
