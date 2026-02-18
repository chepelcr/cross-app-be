from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None)
    slug: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    background_color: Optional[str] = Field(None, alias="backgroundColor")
    button_color: Optional[str] = Field(None, alias="buttonColor")
    image_1_url: Optional[str] = Field(None, alias="image1Url")
    image_2_url: Optional[str] = Field(None, alias="image2Url")
    sort_order: Optional[int] = Field(None, alias="sortOrder")
