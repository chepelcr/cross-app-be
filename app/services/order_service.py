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
from app.repositories.client_repository import ClientRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.store_repository import StoreRepository
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
from app.utils.crossdocking_utils import decode_excel_file

logger = logging.getLogger(__name__)

EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _sync_organization(org_repo: OrganizationRepository, organization_id: str, parsed) -> None:
    """Upsert organization from parsed data."""
    supplier_name = getattr(parsed, "supplier_name", None) or ""
    supplier_gln = getattr(parsed, "supplier_gln", None) or ""
    
    org_repo.upsert(
        organization_id=organization_id,
        name=supplier_name or None,
        gln=supplier_gln or None,
    )


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

        # Upsert normalized entities using shared session
        org_repo = OrganizationRepository.from_session(repo.session)
        client_repo = ClientRepository.from_session(repo.session)
        store_repo = StoreRepository.from_session(repo.session)
        dept_repo = DepartmentRepository.from_session(repo.session)
        product_repo = ProductRepository.from_session(repo.session)

        # Sync organization data from external API
        _sync_organization(org_repo, organization_id, parsed)

        # Upsert client
        client = client_repo.upsert(
            company_id=organization_id,
            client_gln=parsed.client_gln,
            client_name=parsed.client_name,
        )

        # Upsert delivery store
        deliver_to_store = None
        if parsed.deliver_to_code:
            deliver_to_store = store_repo.upsert_by_code(
                company_id=organization_id,
                client_id=client.client_id,
                store_code=parsed.deliver_to_code,
                store_name=parsed.deliver_to_name,
            )

        # Upsert department
        department_entity = None
        if parsed.department:
            department_entity = dept_repo.upsert_by_code(
                company_id=organization_id,
                client_id=client.client_id,
                department_code=parsed.department,
                supplier_code=parsed.supplier_internal_code,
            )

        order = Order(
            company_id=organization_id,
            document_number=parsed.document_number,
            creation_date=parsed.creation_date,
            delivery_date=parsed.delivery_date,
            order_status="pending",
            subtotal=parsed.subtotal,
            discounts=parsed.discounts,
            net_total=parsed.net_total,
            taxes=parsed.taxes,
            grand_total=parsed.grand_total,
            total_quantities=parsed.total_quantities,
            line_count=parsed.line_count,
            document_type=parsed.document_type,
            bgm011=parsed.bgm011,
            order_type=parsed.order_type,
            event=parsed.event,
            latitude=parsed.latitude,
            longitude=parsed.longitude,
            comment=parsed.comment,
            # Normalized FKs
            client_id=client.client_id,
            deliver_to_store_id=deliver_to_store.store_id if deliver_to_store else None,
            department_id=department_entity.department_id if department_entity else None,
        )

        for ln in parsed.lines:
            # Upsert product for each line
            product = product_repo.upsert_by_internal_code(
                company_id=organization_id,
                internal_code=ln.internal_code,
                description=ln.description,
                code=ln.code,
                client_article_code=ln.client_article_code,
                units_per_box=ln.units_per_box,
                price=ln.unit_price,
            )

            order.lines.append(
                OrderLine(
                    line_number=ln.line_number,
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
                    product_id=product.id,
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

        store_repo = StoreRepository.from_session(repo.session)
        product_repo = ProductRepository.from_session(repo.session)

        _apply_crossdocking_data(order, parsed, organization_id, store_repo, product_repo)
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

        org_repo = OrganizationRepository.from_session(repo.session)
        client_repo = ClientRepository.from_session(repo.session)
        store_repo = StoreRepository.from_session(repo.session)
        dept_repo = DepartmentRepository.from_session(repo.session)
        product_repo = ProductRepository.from_session(repo.session)

        # Re-parse order Excel if stored
        if order.excel_url:
            try:
                excel_bytes = download_from_s3(order.excel_url)
                parsed = parse_order_detail_file(BytesIO(excel_bytes))

                # Sync organization
                _sync_organization(org_repo, organization_id, parsed)

                # Upsert normalized entities
                _upsert_order_entities(
                    order, parsed, organization_id,
                    client_repo, store_repo, dept_repo, product_repo,
                )

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

                _apply_crossdocking_data(order, parsed_cd, organization_id, store_repo, product_repo)
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


def _upsert_order_entities(
    order: Order,
    parsed,
    organization_id: str,
    client_repo: ClientRepository,
    store_repo: StoreRepository,
    dept_repo: DepartmentRepository,
    product_repo: ProductRepository,
) -> None:
    """Upsert normalized entities from parsed data and set FKs on the order."""
    client = client_repo.upsert(
        company_id=organization_id,
        client_gln=parsed.client_gln,
        client_name=parsed.client_name,
    )
    order.client_id = client.client_id

    if parsed.deliver_to_code:
        store = store_repo.upsert_by_code(
            company_id=organization_id,
            client_id=client.client_id,
            store_code=parsed.deliver_to_code,
            store_name=parsed.deliver_to_name,
        )
        order.deliver_to_store_id = store.store_id

    if parsed.department:
        dept = dept_repo.upsert_by_code(
            company_id=organization_id,
            client_id=client.client_id,
            department_code=parsed.department,
            supplier_code=parsed.supplier_internal_code,
        )
        order.department_id = dept.department_id

    # Upsert products and set FKs on lines
    order.lines.clear()
    for ln in parsed.lines:
        product = product_repo.upsert_by_internal_code(
            company_id=organization_id,
            internal_code=ln.internal_code,
            description=ln.description,
            code=ln.code,
            client_article_code=ln.client_article_code,
            units_per_box=ln.units_per_box,
            price=ln.unit_price,
        )
        order.lines.append(
            OrderLine(
                line_number=ln.line_number,
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
                product_id=product.id,
            )
        )


def _update_order_from_parsed(order: Order, parsed) -> None:
    """Update order entity fields from a parsed result (without touching lines — handled by _upsert_order_entities)."""
    order.creation_date = parsed.creation_date
    order.delivery_date = parsed.delivery_date
    order.subtotal = parsed.subtotal
    order.discounts = parsed.discounts
    order.net_total = parsed.net_total
    order.taxes = parsed.taxes
    order.grand_total = parsed.grand_total
    order.total_quantities = parsed.total_quantities
    order.line_count = parsed.line_count
    order.document_type = parsed.document_type
    order.bgm011 = parsed.bgm011
    order.order_type = parsed.order_type
    order.event = parsed.event
    order.latitude = parsed.latitude
    order.longitude = parsed.longitude
    order.comment = parsed.comment


def _apply_crossdocking_data(
    order: Order,
    parsed,
    organization_id: str,
    store_repo: StoreRepository,
    product_repo: ProductRepository,
) -> None:
    """Apply parsed crossdocking data to order's sale points with normalized upserts."""
    order.crossdocking_sale_points.clear()
    for sp_data in parsed.crossdocking.sale_points:
        # Upsert store for this sale point
        store = None
        slot_id = ""
        if sp_data.store_number and order.client_id:
            store = store_repo.upsert_by_code(
                company_id=organization_id,
                client_id=order.client_id,
                store_code=sp_data.store_number,
                store_name=sp_data.store_name,
            )
            slot_id = store.slot_id or ""

        sp = CrossDockingSalePoint(
            full_name=sp_data.full_name,
            total_boxes=sp_data.total_boxes,
            total_units=sp_data.total_units,
            store_id=store.store_id if store else None,
        )
        for it_data in sp_data.items:
            # Upsert product for this item
            product = product_repo.upsert_by_internal_code(
                company_id=organization_id,
                internal_code=it_data.internal_code,
                description=it_data.description,
                original_code=it_data.original_code,
                units_per_box=it_data.units_per_box,
            )
            sp.items.append(
                CrossDockingItem(
                    quantity=it_data.quantity,
                    total_units=it_data.total_units,
                    sent=it_data.sent,
                    missing=it_data.missing,
                    product_id=product.id,
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
