from app.dtos import (
    CrossDockingData,
    ItemResponse,
    LocationDTO,
    OrderAttachmentsDTO,
    OrderDetailLineResponse,
    OrderDetailTotals,
    OrderListResponse,
    OrderResponse,
    PaginationResponse,
    PartyDTO,
    SalePointResponse,
    CrossDockingAttachmentsDTO,
)
from app.models.order import Order
from app.utils.crossdocking_utils import build_summaries


def order_to_response(order: Order) -> OrderResponse:
    """Map an Order entity to an OrderResponse DTO."""
    lines = [
        OrderDetailLineResponse(
            line_number=ln.line_number or 0,
            internal_code=ln.internal_code or "",
            code=ln.code or "",
            client_article_code=ln.client_article_code or "",
            description=ln.description or "",
            units_per_box=ln.units_per_box or 0,
            quantity_ordered=ln.quantity_ordered or 0,
            units_ordered=ln.units_ordered or 0,
            unit_price=float(ln.unit_price or 0),
            discount=float(ln.discount or 0),
            line_total=float(ln.line_total or 0),
            tax=float(ln.tax or 0),
            quantity_dispatched=ln.quantity_dispatched or 0,
            dispatch_rejection_reason=ln.dispatch_rejection_reason,
            quantity_received=ln.quantity_received or 0,
            article_code=ln.article_code or "",
        )
        for ln in (order.lines or [])
    ]

    order_totals = None
    if lines:
        order_totals = OrderDetailTotals(
            total_lines=len(lines),
            total_quantity_ordered=sum(ln.quantity_ordered for ln in lines),
            total_units_ordered=sum(ln.units_ordered for ln in lines),
            total_quantity_dispatched=sum(ln.quantity_dispatched for ln in lines),
            total_quantity_received=sum(ln.quantity_received for ln in lines),
            subtotal=float(order.subtotal or 0),
            net_total=float(order.net_total or 0),
            grand_total=float(order.grand_total or 0),
        )

    crossdocking = None
    if order.crossdocking_sale_points:
        crossdocking = build_crossdocking_data(order)

    return OrderResponse(
        order_id=order.order_id,
        company_id=order.company_id,
        document_number=order.document_number,
        document_type=order.document_type,
        bgm011=order.bgm011,
        confirmation_id=order.confirmation_id,
        confirmation_number=order.confirmation_number,
        order_type=order.order_type,
        creation_date=order.creation_date,
        delivery_date=order.delivery_date,
        order_status=order.order_status or "pending",
        client=PartyDTO(
            name=order.client_name,
            gln=order.client_gln,
            internal_code=None,
        ) if order.client_name or order.client_gln else None,
        supplier=PartyDTO(
            name=order.supplier_name,
            gln=order.supplier_gln,
            internal_code=order.supplier_internal_code,
        ) if order.supplier_name or order.supplier_gln else None,
        delivery_location=LocationDTO(
            code=order.deliver_to_code,
            name=order.deliver_to_name,
            gln=order.dispatch_gln,
            latitude=order.latitude,
            longitude=order.longitude,
        ) if order.deliver_to_code or order.deliver_to_name or order.dispatch_gln or order.latitude or order.longitude else None,
        event=order.event,
        department=order.department,
        comment=order.comment,
        line_count=order.line_count,
        total_quantities=order.total_quantities,
        subtotal=float(order.subtotal or 0),
        discounts=float(order.discounts or 0),
        net_total=float(order.net_total or 0),
        taxes=float(order.taxes or 0),
        grand_total=float(order.grand_total or 0),
        attachments=OrderAttachmentsDTO(
            pdf_url=order.pdf_url,
            excel_url=order.excel_url,
            nuevo_reporte_url=order.nuevo_reporte_url,
        ) if order.pdf_url or order.excel_url or order.nuevo_reporte_url else None,
        lines=lines,
        order_totals=order_totals,
        crossdocking=crossdocking,
    )


def orders_to_list_response(orders: list, page: int, page_size: int, total: int) -> OrderListResponse:
    """Map a list of Order entities to an OrderListResponse DTO."""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return OrderListResponse(
        data=[order_to_response(o) for o in orders],
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def build_crossdocking_data(order: Order) -> CrossDockingData:
    """Build the CrossDockingData DTO from an Order's sale points."""
    sale_points = []
    for sp in order.crossdocking_sale_points:
        items = [
            ItemResponse(
                internal_code=it.internal_code or "",
                original_code=it.original_code or "",
                description=it.description or "",
                quantity=it.quantity or 0,
                units_per_box=it.units_per_box or 0,
                total_units=it.total_units or 0,
                sent=it.sent or 0,
                missing=it.missing or 0,
            )
            for it in (sp.items or [])
        ]
        sale_points.append(
            SalePointResponse(
                store_number=sp.store_number or "",
                store_name=sp.store_name or "",
                full_name=sp.full_name or "",
                slot_id=sp.slot_id or "",
                items=items,
                total_boxes=sp.total_boxes or 0,
                total_units=sp.total_units or 0,
            )
        )

    item_summary, box_summary, totals = build_summaries(sale_points)

    return CrossDockingData(
        attachments=CrossDockingAttachmentsDTO(
            pdf_url=order.crossdocking_pdf_url,
            excel_url=order.crossdocking_excel_url,
        ) if order.crossdocking_pdf_url or order.crossdocking_excel_url else None,
        sale_points=sale_points,
        item_summary=item_summary,
        box_summary=box_summary,
        totals=totals,
    )
