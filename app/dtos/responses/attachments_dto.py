"""Attachments DTO - Base document attachments."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AttachmentsDTO(BaseModel):
    """Base document attachments."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    pdf_url: Optional[str] = Field(
        None,
        description="URL to PDF document"
    )
    
    excel_url: Optional[str] = Field(
        None,
        description="URL to Excel document"
    )
