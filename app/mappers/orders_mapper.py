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
    lines = []
    for ln in (order.lines or []):
        p = ln.product
        lines.append(
            OrderDetailLineResponse(
                line_number=ln.line_number or 0,
                internal_code=(p.internal_code if p else "") or "",
                code=(p.code if p else "") or "",
                client_article_code=(p.client_article_code if p else "") or "",
                description=(p.description if p else "") or "",
                units_per_box=(p.units_per_box if p else 0) or 0,
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
        )

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

    # Build client DTO from relationship
    client_dto = None
    if order.client:
        client_dto = PartyDTO(
            name=order.client.client_name,
            gln=order.client.client_gln,
        )

    # Build supplier DTO from organization relationship
    supplier_dto = None
    if order.organization:
        supplier_dto = PartyDTO(
            name=order.organization.name,
            gln=order.organization.gln,
            internal_code=order.organization.internal_code,
            logo_url=order.organization.logo_url,
        )

    # Build delivery location from store relationship
    delivery_location_dto = None
    if order.deliver_to_store:
        delivery_location_dto = LocationDTO(
            code=order.deliver_to_store.store_code,
            name=order.deliver_to_store.store_name,
            latitude=order.latitude,
            longitude=order.longitude,
        )
    elif order.latitude or order.longitude:
        delivery_location_dto = LocationDTO(
            latitude=order.latitude,
            longitude=order.longitude,
        )

    # Department from relationship
    department_value = order.department_rel.department_code if order.department_rel else None

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
        client=client_dto,
        supplier=supplier_dto,
        delivery_location=delivery_location_dto,
        event=order.event,
        department=department_value,
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
        store = sp.store
        items = []
        for it in (sp.items or []):
            p = it.product
            items.append(
                ItemResponse(
                    internal_code=(p.internal_code if p else "") or "",
                    original_code=(p.original_code if p else "") or "",
                    description=(p.description if p else "") or "",
                    quantity=it.quantity or 0,
                    units_per_box=(p.units_per_box if p else 0) or 0,
                    total_units=it.total_units or 0,
                    sent=it.sent or 0,
                    missing=it.missing or 0,
                )
            )
        sale_points.append(
            SalePointResponse(
                store_number=(store.store_code if store else "") or "",
                store_name=(store.store_name if store else "") or "",
                full_name=sp.full_name or "",
                slot_id=(store.slot_id if store else "") or "",
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
