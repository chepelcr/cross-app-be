"""Order Attachments DTO - Order document attachments."""

from typing import Optional
from pydantic import Field

from .attachments_dto import AttachmentsDTO


class OrderAttachmentsDTO(AttachmentsDTO):
    """Order document attachments."""
    
    nuevo_reporte_url: Optional[str] = Field(
        None,
        description="URL to Nuevo Reporte Excel document"
    )
