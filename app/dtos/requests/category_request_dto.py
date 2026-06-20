from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.files import ImageDTO


class CategoryRequestDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None)
    slug: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    background_color: Optional[str] = Field(None)
    button_color: Optional[str] = Field(None)
    image_1: Optional[ImageDTO] = Field(None)
    image_2: Optional[ImageDTO] = Field(None)
    # Preferred path: an already-uploaded asset URL (org media library / S3).
    # When provided, it is stored directly and no blob upload happens. An empty
    # string clears the field.
    image1_url: Optional[str] = Field(None)
    image2_url: Optional[str] = Field(None)
    sort_order: Optional[int] = Field(None)
