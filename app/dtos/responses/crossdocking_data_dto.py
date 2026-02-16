"""Crossdocking Data DTO - Main crossdocking distribution information."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .crossdocking_attachments_dto import CrossDockingAttachmentsDTO
from .crossdocking_sale_point_dto import CrossDockingSalePointDTO
from .crossdocking_item_summary_dto import CrossDockingItemSummaryDTO
from .crossdocking_box_summary_dto import CrossDockingBoxSummaryDTO
from .crossdocking_totals_dto import CrossDockingTotalsDTO


class CrossDockingDataDTO(BaseModel):
    """Crossdocking distribution data."""
    
    model_config = ConfigDict(populate_by_name=True)
    
    attachments: Optional[CrossDockingAttachmentsDTO] = Field(
        None,
        description="Crossdocking document attachments"
    )
    sale_points: list[CrossDockingSalePointDTO] = Field(
        default_factory=list,
        description="Sale points distribution"
    )
    item_summary: list[CrossDockingItemSummaryDTO] = Field(
        default_factory=list,
        description="Item summary"
    )
    box_summary: list[CrossDockingBoxSummaryDTO] = Field(
        default_factory=list,
        description="Box summary"
    )
    totals: CrossDockingTotalsDTO = Field(
        ...,
        description="Crossdocking totals"
    )
