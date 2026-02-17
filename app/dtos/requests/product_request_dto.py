from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ImageDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    data: str = Field(..., alias="data", description="Base64-encoded image data")
    name: Optional[str] = Field(None, alias="name", description="Filename (e.g. product.png)")
    content_type: str = Field(..., alias="contentType", description="MIME type (e.g. image/png)")


class ProductRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    internal_code: Optional[str] = Field(None, alias="internalCode")
    original_code: Optional[str] = Field(None, alias="originalCode")
    client_article_code: Optional[str] = Field(None, alias="clientArticleCode")
    code: Optional[str] = Field(None, alias="code")
    name: Optional[str] = Field(None, alias="name")
    description: Optional[str] = Field(None, alias="description")
    units_per_box: Optional[int] = Field(None, alias="unitsPerBox")
    price: Optional[int] = Field(None, alias="price")
    sku: Optional[str] = Field(None, alias="sku")
    category_id: Optional[str] = Field(None, alias="categoryId")
    image: Optional[ImageDTO] = Field(None, alias="image")
