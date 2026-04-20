from app.dtos.responses.crossdocking_dto import (
    BoxSummary,
    CrossDockingData,
    CrossDockingTotals,
    ItemResponse,
    ItemSummary,
    SalePointResponse,
)
from app.dtos.responses.order_dto import (
    OrderDetailLineResponse,
    OrderDetailTotals,
    OrderListResponse,
    OrderResponse,
)
from app.dtos.responses.pagination_dto import PaginationResponse
from app.dtos.responses.party_dto import PartyDTO
from app.dtos.responses.location_dto import LocationDTO
from app.dtos.responses.attachments_dto import AttachmentsDTO
from app.dtos.responses.order_attachments_dto import OrderAttachmentsDTO
from app.dtos.responses.crossdocking_attachments_dto import CrossDockingAttachmentsDTO
from app.dtos.responses.confirmation_response_dto import (
    ConfirmationOrderSummary,
    ConfirmationResponse,
    ConfirmationListResponse,
)
from app.dtos.responses.branch_dto import BranchResponse, BranchListResponse
from app.dtos.responses.terminal_dto import TerminalResponse, TerminalListResponse
from app.dtos.responses.session_dto import SessionResponse, SessionListResponse
from app.dtos.responses.assignment_dto import AssignmentResponse, AssignmentListResponse
from app.dtos.responses.closing_dto import ClosingResponse, ClosingListResponse
from app.dtos.responses.dashboard_data_dto import (
    DashboardDataResponse,
    StandData,
    ProductRanking,
)

# Backward compatibility
DocumentAttachmentsDTO = OrderAttachmentsDTO

__all__ = [
    "ItemResponse",
    "SalePointResponse",
    "ItemSummary",
    "BoxSummary",
    "CrossDockingTotals",
    "CrossDockingData",
    "OrderDetailLineResponse",
    "OrderDetailTotals",
    "OrderResponse",
    "OrderListResponse",
    "PaginationResponse",
    "PartyDTO",
    "LocationDTO",
    "AttachmentsDTO",
    "OrderAttachmentsDTO",
    "CrossDockingAttachmentsDTO",
    "DocumentAttachmentsDTO",
    "ConfirmationOrderSummary",
    "ConfirmationResponse",
    "ConfirmationListResponse",
    "BranchResponse",
    "BranchListResponse",
    "TerminalResponse",
    "TerminalListResponse",
    "SessionResponse",
    "SessionListResponse",
    "AssignmentResponse",
    "AssignmentListResponse",
    "ClosingResponse",
    "ClosingListResponse",
    "DashboardDataResponse",
    "StandData",
    "ProductRanking",
]
