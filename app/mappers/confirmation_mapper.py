from app.dtos.responses.confirmation_response_dto import (
    ConfirmationListResponse,
    ConfirmationOrderSummary,
    ConfirmationResponse,
)
from app.dtos.responses.pagination_dto import PaginationResponse
from app.models.confirmation import Confirmation


def confirmation_to_response(confirmation: Confirmation) -> ConfirmationResponse:
    orders = [
        ConfirmationOrderSummary(
            order_id=o.order_id,
            document_number=o.document_number,
            delivery_date=o.delivery_date,
            deliver_to_code=o.deliver_to_code,
            deliver_to_name=o.deliver_to_name,
            order_status=o.order_status,
        )
        for o in (confirmation.orders or [])
        if o.status == 1
    ]

    return ConfirmationResponse(
        confirmation_id=confirmation.confirmation_id,
        company_id=confirmation.company_id,
        confirmation_number=confirmation.confirmation_number,
        delivery_date=confirmation.delivery_date,
        deliver_to_code=confirmation.deliver_to_code,
        deliver_to_name=confirmation.deliver_to_name,
        confirmation_status=confirmation.confirmation_status or "pending",
        orders=orders,
    )


def confirmations_to_list_response(
    confirmations: list, page: int, page_size: int, total: int
) -> ConfirmationListResponse:
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return ConfirmationListResponse(
        data=[confirmation_to_response(c) for c in confirmations],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )
