from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.files import ImageDTO


class CategoryRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None)
    slug: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    background_color: Optional[str] = Field(None, alias="backgroundColor")
    button_color: Optional[str] = Field(None, alias="buttonColor")
    image_1: Optional[ImageDTO] = Field(None, alias="image1")
    image_2: Optional[ImageDTO] = Field(None, alias="image2")
    sort_order: Optional[int] = Field(None, alias="sortOrder")
