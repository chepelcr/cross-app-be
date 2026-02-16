"""Crossdocking DTOs - Re-exports for backward compatibility."""

from .crossdocking_item_dto import CrossDockingItemDTO
from .crossdocking_sale_point_dto import CrossDockingSalePointDTO
from .crossdocking_item_summary_dto import CrossDockingItemSummaryDTO
from .crossdocking_box_summary_dto import CrossDockingBoxSummaryDTO
from .crossdocking_totals_dto import CrossDockingTotalsDTO
from .crossdocking_attachments_dto import CrossDockingAttachmentsDTO
from .crossdocking_data_dto import CrossDockingDataDTO

# Backward compatibility aliases
ItemResponse = CrossDockingItemDTO
SalePointResponse = CrossDockingSalePointDTO
ItemSummary = CrossDockingItemSummaryDTO
BoxSummary = CrossDockingBoxSummaryDTO
CrossDockingTotals = CrossDockingTotalsDTO
CrossDockingData = CrossDockingDataDTO

__all__ = [
    "CrossDockingItemDTO",
    "CrossDockingSalePointDTO",
    "CrossDockingItemSummaryDTO",
    "CrossDockingBoxSummaryDTO",
    "CrossDockingTotalsDTO",
    "CrossDockingAttachmentsDTO",
    "CrossDockingDataDTO",
    "ItemResponse",
    "SalePointResponse",
    "ItemSummary",
    "BoxSummary",
    "CrossDockingTotals",
    "CrossDockingData",
]
