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

    ticket_url: Optional[str] = Field(
        None,
        description=(
            "80mm thermal ticket PDF (TSR-127). Generated server-side like the "
            "other documents, so a re-print is byte-identical to the original."
        )
    )
