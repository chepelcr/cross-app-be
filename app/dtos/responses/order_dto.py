"""Order DTOs - Re-exports for backward compatibility."""

from .order_detail_line_dto import OrderDetailLineResponse
from .order_detail_totals_dto import OrderDetailTotals
from .order_response_dto import OrderResponse
from .pagination_dto import PaginationResponse
from .order_list_dto import OrderListResponse
from .party_dto import PartyDTO
from .location_dto import LocationDTO
from .attachments_dto import AttachmentsDTO
from .order_attachments_dto import OrderAttachmentsDTO
from .crossdocking_attachments_dto import CrossDockingAttachmentsDTO

# Backward compatibility
DocumentAttachmentsDTO = OrderAttachmentsDTO

__all__ = [
    "OrderDetailLineResponse",
    "OrderDetailTotals",
    "OrderResponse",
    "PaginationResponse",
    "OrderListResponse",
    "PartyDTO",
    "LocationDTO",
    "AttachmentsDTO",
    "OrderAttachmentsDTO",
    "CrossDockingAttachmentsDTO",
    "DocumentAttachmentsDTO",
]
