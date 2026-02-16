from typing import Optional
from pydantic import BaseModel, Field


class ExcelFileDTO(BaseModel):
    data: str = Field(..., description="Base64 encoded Excel file data")
    name: Optional[str] = Field(None, description="File name without extension")
    content_type: Optional[str] = Field(
        None,
        alias="contentType",
        description="MIME type (e.g. application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)",
    )

    model_config = {"populate_by_name": True}
