from __future__ import annotations

import logging
from io import BytesIO

from app.dtos import ExcelFileDTO, OrderListResponse, OrderResponse
from app.dtos.responses.order_dto import PaginationResponse
from app.mappers.orders_mapper import build_crossdocking_data, order_to_response
from app.models.crossdocking_item import CrossDockingItem
from app.models.crossdocking_sale_point import CrossDockingSalePoint
from app.models.order import Order
from app.models.order_line import OrderLine
from app.repositories.order_repository import OrderRepository
from app.utils.search_utils import SearchUtils
from app.services.excel_export_service import create_nuevo_reporte
from app.services.excel_parser import parse_crossdocking_file
from app.services.order_detail_parser import parse_order_detail_file
from app.services.pdf_service import (
    _s3_key,
    create_crossdocking_pdf,
    create_order_pdf,
    download_from_s3,
    upload_file_to_s3,
)
from app.services.store_slot_service import get_slot_map
from app.utils.crossdocking_utils import decode_excel_file

logger = logging.getLogger(__name__)

EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def process_order_excel(organization_id: str, body: ExcelFileDTO) -> OrderResponse:
    """Decode Excel, parse DETALLES, save order to DB, generate PDF, and return OrderResponse."""
    file = decode_excel_file(body)
    excel_bytes = file.getvalue()
    file.seek(0)
    parsed = parse_order_detail_file(file)

    with OrderRepository() as repo:
        existing = repo.find_by_company_and_document(organization_id, parsed.document_number)
        if existing:
            raise ValueError(
                f"Order {parsed.document_number} already exists for organization {organization_id}"
            )

        order = Order(
            company_id=organization_id,
            document_number=parsed.document_number,
            client_name=parsed.client_name,
            creation_date=parsed.creation_date,
            delivery_date=parsed.delivery_date,
            order_status="pending",
            deliver_to_code=parsed.deliver_to_code,
            deliver_to_name=parsed.deliver_to_name,
            subtotal=parsed.subtotal,
            discounts=parsed.discounts,
            net_total=parsed.net_total,
            taxes=parsed.taxes,
            grand_total=parsed.grand_total,
            total_quantities=parsed.total_quantities,
            supplier_name=parsed.supplier_name,
            client_gln=parsed.client_gln,
            line_count=parsed.line_count,
            dispatch_gln=parsed.dispatch_gln,
            document_type=parsed.document_type,
            supplier_gln=parsed.supplier_gln,
            supplier_internal_code=parsed.supplier_internal_code,
            bgm011=parsed.bgm011,
            order_type=parsed.order_type,
            event=parsed.event,
            department=parsed.department,
            latitude=parsed.latitude,
            longitude=parsed.longitude,
            comment=parsed.comment,
        )

        for ln in parsed.lines:
            order.lines.append(
                OrderLine(
                    line_number=ln.line_number,
                    internal_code=ln.internal_code,
                    code=ln.code,
                    client_article_code=ln.client_article_code,
                    description=ln.description,
                    units_per_box=ln.units_per_box,
                    quantity_ordered=ln.quantity_ordered,
                    units_ordered=ln.units_ordered,
                    unit_price=ln.unit_price,
                    discount=ln.discount,
                    line_total=ln.line_total,
                    tax=ln.tax,
                    quantity_dispatched=ln.quantity_dispatched,
                    dispatch_rejection_reason=ln.dispatch_rejection_reason,
                    quantity_received=ln.quantity_received,
                    article_code=ln.article_code,
                )
            )

        order = repo.save(order)

        # Upload original Excel to S3
        try:
            last4 = (parsed.document_number or "")[-4:]
            excel_key = _s3_key(organization_id, parsed.document_number, f"{last4}-DT.xlsx")
            order.excel_url = upload_file_to_s3(excel_bytes, excel_key, EXCEL_CONTENT_TYPE)
        except Exception as e:
            logger.warning(f"Excel upload failed for order {order.document_number}: {e}")

        try:
            pdf_url = create_order_pdf(order)
            order.pdf_url = pdf_url
        except Exception as e:
            logger.warning(f"PDF generation failed for order {order.document_number}: {e}")

        order = repo.save(order)
        return order_to_response(order)


def process_crossdocking_excel(
    organization_id: str, document_number: str, body: ExcelFileDTO
) -> OrderResponse:
    """Decode Excel, parse crossdocking, validate, update sale points on existing order."""
    file = decode_excel_file(body)
    cd_bytes = file.getvalue()
    file.seek(0)
    parsed = parse_crossdocking_file(file)

    if parsed.document_number and parsed.document_number != document_number:
        raise ValueError(
            f"Crossdocking file document number '{parsed.document_number}' "
            f"does not match order '{document_number}'"
        )

    # Look up slot_ids from store_slots reference table
    slot_map = {}
    try:
        slot_map = get_slot_map()
    except Exception as e:
        logger.warning(f"Could not load store slot map: {e}")

    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}. "
                "You must upload the order details (DETALLES) file first."
            )

        if not order.lines:
            raise ValueError(
                f"Order {document_number} has no detail lines. "
                "Upload the order details (DETALLES) file first."
            )

        _apply_crossdocking_data(order, parsed, slot_map)
        order.order_status = "processing"
        order = repo.save(order)

        # Upload original crossdocking Excel to S3
        try:
            last4 = (document_number or "")[-4:]
            cd_key = _s3_key(organization_id, document_number, f"{last4}-CD.xlsx")
            order.crossdocking_excel_url = upload_file_to_s3(cd_bytes, cd_key, EXCEL_CONTENT_TYPE)
        except Exception as e:
            logger.warning(f"Crossdocking Excel upload failed: {e}")

        # Generate crossdocking PDF and NuevoReporte Excel
        _generate_crossdocking_outputs(order)

        order = repo.save(order)
        return order_to_response(order)


def get_order(organization_id: str, document_number: str) -> OrderResponse:
    """Get order by company and document number. Generates PDF if missing."""
    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}"
            )

        if not order.pdf_url:
            try:
                pdf_url = create_order_pdf(order)
                order.pdf_url = pdf_url
                order = repo.save(order)
                logger.info(f"Generated missing PDF for order {document_number}: {pdf_url}")
            except Exception as e:
                logger.warning(
                    f"Failed to generate missing PDF for order {document_number}: {e}"
                )

        if order.crossdocking_sale_points and not order.crossdocking_pdf_url:
            try:
                crossdocking_data = build_crossdocking_data(order)
                cd_pdf_url = create_crossdocking_pdf(order, crossdocking_data)
                order.crossdocking_pdf_url = cd_pdf_url
                order = repo.save(order)
                logger.info(f"Generated missing crossdocking PDF: {cd_pdf_url}")
            except Exception as e:
                logger.warning(f"Failed to generate crossdocking PDF: {e}")

        if order.crossdocking_sale_points and not order.nuevo_reporte_url:
            try:
                crossdocking_data = build_crossdocking_data(order)
                nr_url = create_nuevo_reporte(order, crossdocking_data)
                order.nuevo_reporte_url = nr_url
                order = repo.save(order)
                logger.info(f"Generated missing NuevoReporte: {nr_url}")
            except Exception as e:
                logger.warning(f"Failed to generate NuevoReporte: {e}")

        return order_to_response(order)


def reprocess_order(organization_id: str, document_number: str) -> OrderResponse:
    """Re-download and re-parse order + crossdocking Excel files, regenerate all outputs."""
    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}"
            )

        # Re-parse order Excel if stored
        if order.excel_url:
            try:
                excel_bytes = download_from_s3(order.excel_url)
                parsed = parse_order_detail_file(BytesIO(excel_bytes))
                _update_order_from_parsed(order, parsed)
                order = repo.save(order)
                logger.info(f"Re-parsed order Excel for {document_number}")
            except Exception as e:
                logger.warning(f"Failed to re-parse order Excel for {document_number}: {e}")

        # Regenerate order PDF
        try:
            order.pdf_url = create_order_pdf(order)
        except Exception as e:
            logger.warning(f"Order PDF regeneration failed for {document_number}: {e}")

        # Re-parse crossdocking Excel if stored
        if order.crossdocking_excel_url:
            try:
                cd_bytes = download_from_s3(order.crossdocking_excel_url)
                parsed_cd = parse_crossdocking_file(BytesIO(cd_bytes))

                slot_map = {}
                try:
                    slot_map = get_slot_map()
                except Exception as e:
                    logger.warning(f"Could not load store slot map: {e}")

                _apply_crossdocking_data(order, parsed_cd, slot_map)
                order.order_status = "processing"
                order = repo.save(order)
                logger.info(f"Re-parsed crossdocking Excel for {document_number}")
            except Exception as e:
                logger.warning(f"Failed to re-parse crossdocking Excel for {document_number}: {e}")

            _generate_crossdocking_outputs(order)

        order = repo.save(order)
        return order_to_response(order)


def get_orders(
    organization_id: str,
    search: str | None = None,
    page: int = 1,
    page_size: int = 12,
) -> OrderListResponse:
    """Get paginated orders for an organization with optional search filters."""
    search_filters = None
    order_by = None

    if search:
        filters, order_result = SearchUtils.parse_search_filter(search, Order)
        if filters:
            search_filters = filters
        if order_result:
            order_by = order_result

    with OrderRepository() as repo:
        orders, total = repo.find_all_by_company(
            organization_id,
            search_filters=search_filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return OrderListResponse(
            data=[order_to_response(o) for o in orders],
            pagination=PaginationResponse(
                page=page,
                pageSize=page_size,
                totalElements=total,
                totalPages=total_pages,
            ),
        )


def update_order_status(organization_id: str, document_number: str, status_code: int) -> OrderResponse:
    """Update order status."""
    status_map = {1: "pending", 2: "processing", 3: "shipped", 4: "delivered", 5: "cancelled"}
    status = status_map.get(status_code)
    if not status:
        raise ValueError(f"Invalid status code: {status_code}")
    
    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}"
            )
        
        order.order_status = status
        order = repo.save(order)
        return order_to_response(order)


def _update_order_from_parsed(order: Order, parsed) -> None:
    """Update order entity fields and lines from a parsed result."""
    order.client_name = parsed.client_name
    order.creation_date = parsed.creation_date
    order.delivery_date = parsed.delivery_date
    order.deliver_to_code = parsed.deliver_to_code
    order.deliver_to_name = parsed.deliver_to_name
    order.subtotal = parsed.subtotal
    order.discounts = parsed.discounts
    order.net_total = parsed.net_total
    order.taxes = parsed.taxes
    order.grand_total = parsed.grand_total
    order.total_quantities = parsed.total_quantities
    order.supplier_name = parsed.supplier_name
    order.client_gln = parsed.client_gln
    order.line_count = parsed.line_count
    order.dispatch_gln = parsed.dispatch_gln
    order.document_type = parsed.document_type
    order.supplier_gln = parsed.supplier_gln
    order.supplier_internal_code = parsed.supplier_internal_code
    order.bgm011 = parsed.bgm011
    order.order_type = parsed.order_type
    order.event = parsed.event
    order.department = parsed.department
    order.latitude = parsed.latitude
    order.longitude = parsed.longitude
    order.comment = parsed.comment

    order.lines.clear()
    for ln in parsed.lines:
        order.lines.append(
            OrderLine(
                line_number=ln.line_number,
                internal_code=ln.internal_code,
                code=ln.code,
                client_article_code=ln.client_article_code,
                description=ln.description,
                units_per_box=ln.units_per_box,
                quantity_ordered=ln.quantity_ordered,
                units_ordered=ln.units_ordered,
                unit_price=ln.unit_price,
                discount=ln.discount,
                line_total=ln.line_total,
                tax=ln.tax,
                quantity_dispatched=ln.quantity_dispatched,
                dispatch_rejection_reason=ln.dispatch_rejection_reason,
                quantity_received=ln.quantity_received,
                article_code=ln.article_code,
            )
        )


def _apply_crossdocking_data(order: Order, parsed, slot_map: dict) -> None:
    """Apply parsed crossdocking data to order's sale points."""
    order.crossdocking_sale_points.clear()
    for sp_data in parsed.crossdocking.sale_points:
        sp = CrossDockingSalePoint(
            store_number=sp_data.store_number,
            store_name=sp_data.store_name,
            full_name=sp_data.full_name,
            total_boxes=sp_data.total_boxes,
            total_units=sp_data.total_units,
            slot_id=slot_map.get(sp_data.store_number, ""),
        )
        for it_data in sp_data.items:
            sp.items.append(
                CrossDockingItem(
                    internal_code=it_data.internal_code,
                    original_code=it_data.original_code,
                    description=it_data.description,
                    quantity=it_data.quantity,
                    units_per_box=it_data.units_per_box,
                    total_units=it_data.total_units,
                    sent=it_data.sent,
                    missing=it_data.missing,
                )
            )
        order.crossdocking_sale_points.append(sp)


def _generate_crossdocking_outputs(order: Order) -> None:
    """Generate crossdocking PDF and NuevoReporte Excel for an order."""
    crossdocking_data = build_crossdocking_data(order)
    try:
        cd_pdf_url = create_crossdocking_pdf(order, crossdocking_data)
        order.crossdocking_pdf_url = cd_pdf_url
        logger.info(f"Crossdocking PDF generated: {cd_pdf_url}")
    except Exception as e:
        logger.warning(f"Crossdocking PDF generation failed: {e}")

    try:
        nr_url = create_nuevo_reporte(order, crossdocking_data)
        order.nuevo_reporte_url = nr_url
        logger.info(f"NuevoReporte generated: {nr_url}")
    except Exception as e:
        logger.warning(f"NuevoReporte generation failed: {e}")
