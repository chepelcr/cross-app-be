from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from typing import Optional

from sqlalchemy import select, text

from app.dtos.files import ExcelDTO, ExcelAndColorDTO
from app.dtos import OrderListResponse, OrderResponse, SelectColorDTO
from app.dtos.requests.manual_order_dto import CreateManualOrderDTO
from app.dtos.requests.product_request_dto import (
    ProductDiscountDTO,
    ProductTaxDTO,
    TaxAmountDTO,
    TaxFactorDTO,
    TaxRateDTO,
    TaxSpecialFieldsDTO,
)
from app.dtos.requests.storefront_order_dto import CreateStorefrontOrderDTO
from app.dtos.responses.storefront_order_dto import StorefrontOrderCreatedResponse
from app.enums.hacienda_codes import DiscountType
from app.enums.order_status import ORDER_STATUS_CODES, can_transition
from app.enums.report_color import ReportColorScheme, get_color_palette
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
from app.enums.search_filters import SearchFilters
from app.utils.search_utils import SearchUtils
from app.services.excel_export_service import create_nuevo_reporte
from app.services.excel_parser import parse_crossdocking_file
from app.services.line_calculation_service import LineCalculator, LineInput
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

#: Numeric status code → status name, inverted from the canonical map so the
#: two can never drift.
_STATUS_BY_CODE = {code: name for name, code in ORDER_STATUS_CODES.items()}

_DEPT_COLOR_MAP = {
    "26": ReportColorScheme.GREEN_ALT.value,
    "22": ReportColorScheme.ORANGE.value,
}


def _default_color_for_order(order: Order) -> str:
    """Return the default color scheme based on department code."""
    dept = order.department_rel
    if dept:
        code = (dept.department_code or "").strip()
        if code in _DEPT_COLOR_MAP:
            return _DEPT_COLOR_MAP[code]
    return ReportColorScheme.GREEN.value

EXCEL_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _sync_organization(org_repo: OrganizationRepository, organization_id: str, parsed) -> None:
    """Upsert organization from parsed data."""
    supplier_name = parsed.supplier_name if hasattr(parsed, "supplier_name") else ""
    supplier_gln = parsed.supplier_gln if hasattr(parsed, "supplier_gln") else ""
    
    org_repo.upsert(
        organization_id=organization_id,
        name=supplier_name or None,
        gln=supplier_gln or None,
    )


def process_order_excel(organization_id: str, body: ExcelDTO) -> OrderResponse:
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
                gln=parsed.dispatch_gln or None,
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

        # Lines are built and costed by the shared builder — see
        # `_rebuild_imported_lines`. It also re-adds the order's totals from
        # the recomputed lines, superseding the header figures assigned above.
        _rebuild_imported_lines(order, parsed, organization_id, product_repo)

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
    organization_id: str, document_number: str, body: ExcelAndColorDTO
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

        # Store selected color (default by department if not specified)
        color = body.color or _default_color_for_order(order)
        order.report_color = color.value if isinstance(color, ReportColorScheme) else str(color)

        order = repo.save(order)

        # Upload original crossdocking Excel to S3
        try:
            last4 = (document_number or "")[-4:]
            cd_key = _s3_key(organization_id, document_number, f"{last4}-CD.xlsx")
            order.crossdocking_excel_url = upload_file_to_s3(cd_bytes, cd_key, EXCEL_CONTENT_TYPE)
        except Exception as e:
            logger.warning(f"Crossdocking Excel upload failed: {e}")

        # Generate crossdocking PDF and NuevoReporte Excel
        _generate_crossdocking_outputs(order, color)

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
                cd_pdf_url = create_crossdocking_pdf(
                    order, crossdocking_data, order.report_color
                )
                order.crossdocking_pdf_url = cd_pdf_url
                order = repo.save(order)
                logger.info(f"Generated missing crossdocking PDF: {cd_pdf_url}")
            except Exception as e:
                logger.warning(f"Failed to generate crossdocking PDF: {e}")

        if order.crossdocking_sale_points and not order.nuevo_reporte_url:
            try:
                crossdocking_data = build_crossdocking_data(order)
                nr_url = create_nuevo_reporte(order, crossdocking_data, order.report_color)
                order.nuevo_reporte_url = nr_url
                order = repo.save(order)
                logger.info(f"Generated missing NuevoReporte: {nr_url}")
            except Exception as e:
                logger.warning(f"Failed to generate NuevoReporte: {e}")

        return order_to_response(order)


def reprocess_order(organization_id: str, document_number: str, color=None) -> OrderResponse:
    """Re-parse the stored Excel files, recompute the money, regenerate outputs.

    Three things happen, in order, and each is independently useful:

    1. the order and crossdocking spreadsheets are re-parsed from S3 when they
       are stored, so a change to the parser reaches an existing order;
    2. **every line's amounts are recomputed through the current discount/tax
       engine** and the order totals re-added from them — this runs even with no
       spreadsheet on file, which is what makes the button a repair tool for
       orders captured before an engine fix;
    3. the PDF, the crossdocking PDF and the Nuevo Reporte are regenerated.
    """
    logger.info(f"[REPROCESS] START order={document_number} org={organization_id} color={color}")
    with OrderRepository() as repo:
        logger.info(f"[REPROCESS] DB session open — finding order")
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}"
            )
        logger.info(f"[REPROCESS] Order found: order_id={order.order_id} excel_url={order.excel_url} cd_excel_url={order.crossdocking_excel_url}")

        org_repo = OrganizationRepository.from_session(repo.session)
        client_repo = ClientRepository.from_session(repo.session)
        store_repo = StoreRepository.from_session(repo.session)
        dept_repo = DepartmentRepository.from_session(repo.session)
        product_repo = ProductRepository.from_session(repo.session)

        # Re-parse order Excel if stored
        if order.excel_url:
            logger.info(f"[REPROCESS] Downloading order Excel from S3: {order.excel_url}")
            try:
                excel_bytes = download_from_s3(order.excel_url)
                logger.info(f"[REPROCESS] Order Excel downloaded ({len(excel_bytes)} bytes) — parsing")
                parsed = parse_order_detail_file(BytesIO(excel_bytes))
                logger.info(f"[REPROCESS] Order Excel parsed — syncing organization")

                # Sync organization
                _sync_organization(org_repo, organization_id, parsed)
                logger.info(f"[REPROCESS] Organization synced — upserting entities")

                # Upsert normalized entities
                _upsert_order_entities(
                    order, parsed, organization_id,
                    client_repo, store_repo, dept_repo, product_repo,
                )
                logger.info(f"[REPROCESS] Entities upserted — updating order from parsed")

                _update_order_from_parsed(order, parsed)
                order = repo.save(order)
                logger.info(f"Re-parsed order Excel for {document_number}")
            except Exception as e:
                logger.warning(f"Failed to re-parse order Excel for {document_number}: {e}", exc_info=True)
        else:
            logger.info(f"[REPROCESS] No order Excel URL — skipping Excel re-parse")

        # Recompute every line's money from its own fiscal detail, and re-add
        # the order totals from the result.
        #
        # This runs whether or not the spreadsheet was re-parsed, and that is
        # the point of the button: an order captured before a fix to the
        # discount/tax engine — or before imported lines carried any structured
        # detail at all — is brought up to what the current code computes,
        # without needing the original file. Lines with no structured detail are
        # left alone (see `_recompute_imported_line`), so a hand-captured order
        # the user edited is never silently re-priced.
        logger.info(f"[REPROCESS] Recomputing line amounts with the current engine")
        try:
            for line in (order.lines or []):
                _recompute_imported_line(line, line.product)
            _resum_order_totals(order)
            order = repo.save(order)
            logger.info(
                f"[REPROCESS] Recomputed {len(order.lines or [])} line(s); "
                f"grand_total={order.grand_total}"
            )
        except Exception as e:
            logger.warning(
                f"Failed to recompute line amounts for {document_number}: {e}",
                exc_info=True,
            )

        # Resolve color: use provided color, or fall back to stored value
        if color is not None:
            resolved_color = color.value if isinstance(color, ReportColorScheme) else str(color)
            order.report_color = resolved_color
        resolved_color = order.report_color or _default_color_for_order(order)
        logger.info(f"[REPROCESS] Resolved color: {resolved_color}")

        # Regenerate order PDF
        logger.info(f"[REPROCESS] Regenerating order PDF")
        try:
            # Ensure all relationships are loaded fresh from database
            repo.session.expire_all()
            order = repo.find_by_company_and_document(organization_id, document_number)
            order.pdf_url = create_order_pdf(order)
            order = repo.save(order)
            logger.info(f"Order PDF regenerated for {document_number}: {order.pdf_url}")
        except Exception as e:
            logger.error(f"Order PDF regeneration failed for {document_number}: {e}", exc_info=True)

        # Re-parse crossdocking Excel if stored
        if order.crossdocking_excel_url:
            logger.info(f"[REPROCESS] Downloading crossdocking Excel: {order.crossdocking_excel_url}")
            try:
                cd_bytes = download_from_s3(order.crossdocking_excel_url)
                logger.info(f"[REPROCESS] CD Excel downloaded ({len(cd_bytes)} bytes) — parsing")
                parsed_cd = parse_crossdocking_file(BytesIO(cd_bytes))
                logger.info(f"[REPROCESS] CD Excel parsed — applying crossdocking data")

                _apply_crossdocking_data(order, parsed_cd, organization_id, store_repo, product_repo)
                order = repo.save(order)
                logger.info(f"Re-parsed crossdocking Excel for {document_number}")
            except Exception as e:
                logger.warning(f"Failed to re-parse crossdocking Excel for {document_number}: {e}", exc_info=True)

            logger.info(f"[REPROCESS] Generating crossdocking outputs (PDF + Excel)")
            _generate_crossdocking_outputs(order, resolved_color)
            logger.info(f"[REPROCESS] Crossdocking outputs generated")
        else:
            logger.info(f"[REPROCESS] No crossdocking Excel URL — skipping CD re-parse")

        logger.info(f"[REPROCESS] Saving final order state")
        order = repo.save(order)
        logger.info(f"[REPROCESS] DONE order={document_number}")
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
        filters, order_result = SearchUtils.parse_search_filter(search, Order, SearchFilters)
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
                page_size=page_size,
                total_elements=total,
                total_pages=total_pages,
            ),
        )


def update_order_status(organization_id: str, document_number: str, status_code: int) -> OrderResponse:
    """Move an order to a new status, refusing illegal jumps.

    Code 0 is `quote` — a proforma (TSR-156). The guard matters most there: a
    quote may only be **approved** into `pending` or cancelled. Letting it jump
    straight to `delivered` would allow an unapproved cotización to be invoiced
    as though the customer had agreed to it.
    """
    status = _STATUS_BY_CODE.get(status_code)
    if not status:
        raise ValueError(
            f"Invalid status code: {status_code} (expected one of {sorted(_STATUS_BY_CODE)})"
        )

    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(
                f"Order {document_number} not found for organization {organization_id}"
            )

        if not can_transition(order.order_status, status):
            raise ValueError(
                f"Cannot move order {document_number} from "
                f"'{order.order_status}' to '{status}'"
            )

        order.order_status = status
        order = repo.save(order)
        return order_to_response(order)


def _generate_tracking_number() -> str:
    """Generate a short, human-friendly public tracking number.

    Format: ``TSU-YYYYMMDD-XXXXXX`` where the suffix is a random uppercase
    alphanumeric token. Used as both the order document number and the public
    tracking handle handed off to WhatsApp.
    """
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no ambiguous chars
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"TSU-{today}-{suffix}"


def create_storefront_order(
    organization_id: str, dto: CreateStorefrontOrderDTO
) -> StorefrontOrderCreatedResponse:
    """Create an anonymous storefront pedido (tracked order, status 'pending').

    Builds an Order from a guest customer (name/phone), a structured CR
    address, a delivery method and line items referencing existing products.
    Totals are computed from the products' net price. Returns the order id and
    a public tracking number.
    """
    with OrderRepository() as repo:
        product_repo = ProductRepository.from_session(repo.session)

        # Generate a unique tracking/document number (retry on the rare clash).
        tracking_number = _generate_tracking_number()
        for _ in range(5):
            if not repo.find_by_company_and_document(organization_id, tracking_number):
                break
            tracking_number = _generate_tracking_number()

        address = dto.address
        order = Order(
            company_id=organization_id,
            document_number=tracking_number,
            tracking_number=tracking_number,
            creation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            order_status="pending",
            order_type="storefront",
            customer_name=dto.customer_name,
            customer_phone=dto.customer_phone,
            delivery_method=dto.delivery_method,
            comment=dto.comment,
            state_id=address.state_id if address else None,
            county_id=address.county_id if address else None,
            district_id=address.district_id if address else None,
            neighborhood_id=address.neighborhood_id if address else None,
            delivery_address=address.address if address else None,
        )

        subtotal = 0.0
        total_quantities = 0
        for idx, item in enumerate(dto.items, start=1):
            product = product_repo.find_by_id_and_company(item.product_id, organization_id)
            if not product:
                raise LookupError(
                    f"Product '{item.product_id}' not found for organization "
                    f"{organization_id}"
                )

            unit_price = float(product.price or 0)
            line_total = unit_price * item.quantity
            subtotal += line_total
            total_quantities += item.quantity

            order.lines.append(
                OrderLine(
                    line_number=idx,
                    quantity_ordered=item.quantity,
                    units_ordered=item.quantity,
                    unit_price=unit_price,
                    discount=0,
                    line_total=line_total,
                    tax=0,
                    product_id=product.id,
                )
            )

        order.subtotal = subtotal
        order.discounts = 0
        order.net_total = subtotal
        order.taxes = 0
        order.grand_total = subtotal
        order.total_quantities = total_quantities
        order.line_count = len(order.lines)

        order = repo.save(order)

        return StorefrontOrderCreatedResponse(
            order_id=order.order_id,
            document_number=order.document_number,
            tracking_number=order.tracking_number or order.document_number,
            order_status=order.order_status or "pending",
            grand_total=float(order.grand_total or 0),
        )


def _imported_line_discounts(discount_amount) -> list | None:
    """Structured discount for a line that came from an Excel import.

    The customer's spreadsheet carries a discount AMOUNT but no discount TYPE,
    and we are not adding a column to it. Every such discount is therefore
    recorded as **07 — Descuento Comercial**, which is the honest reading of a
    supplier's trade discount and, unlike 99, needs no free-text reason.

    Choosing 07 also matters fiscally: only 01 (regalía) and 03 (bonificación)
    re-route IVA into `ImpuestoAsumidoEmisorFabrica` (Nota 20), so a commercial
    discount stays a plain price reduction rather than becoming a factory-
    assumed tax.
    """
    amount = float(discount_amount or 0)
    if amount <= 0:
        return None
    return [
        {
            "discount_type_id": DiscountType.COMMERCIAL.value,
            "is_amount": True,
            "amount": amount,
            "reason": None,  # 07 needs none; only 99 does.
        }
    ]


def _imported_line_taxes(product) -> list | None:
    """Carry the product's configured taxes onto the imported line.

    The Excel has no tax structure either — only a total. Copying the product's
    own `taxes` gives the line the same shape a POS-captured line has, which is
    what lets an imported order be billed later without inventing a rate.

    The stored JSONB is already ProductTaxDTO-shaped, so it is copied verbatim;
    the per-row `amount` is dropped, because the product's figure was computed
    against the PRODUCT's own price and quantity and says nothing about this
    line's. `_recompute_imported_line` derives the real amounts from the order
    quantity.
    """
    taxes = getattr(product, "taxes", None)
    if not taxes:
        return None
    out = []
    for t in taxes:
        row = dict(t)
        row.pop("amount", None)
        out.append(row)
    return out


def _imported_line_net_price(parsed_line, product) -> float:
    """Unit price BEFORE tax for an imported line.

    The product's configured `unit_price` wins when it has one: that is the
    fiscal net price the org maintains in its catalog, and it is the number the
    taxes on the very same product were configured against. The spreadsheet's
    unit price is the fallback — on a chain order it is the negotiated price and
    is already net of tax, which is why it is usable at all.
    """
    catalog_net = getattr(product, "unit_price", None)
    if catalog_net is not None and float(catalog_net) > 0:
        return float(catalog_net)
    return float(parsed_line.unit_price or 0)


def _allocate_header_discount(parsed) -> dict[int, float]:
    """Spread an order-level discount across the lines that have none.

    Real Walmart spreadsheets routinely carry `0` in every line's discount
    column while the header totals a discount for the whole order. Taken
    literally that produces lines summing to more than the order, and an invoice
    built from them overcharges the customer by exactly the missing discount.

    So when NO line declares a discount and the header does, the header amount
    is allocated across the lines in proportion to their gross — the same
    apportionment the chain applies at their end — and the remainder from
    rounding lands on the largest line, so the parts add back to the whole
    exactly. Returned keyed by line number; empty when the lines already carry
    their own discounts, which are then authoritative and left alone.
    """
    header_discount = Decimal(str(getattr(parsed, "discounts", 0) or 0))
    if header_discount <= 0:
        return {}

    lines = list(parsed.lines or [])
    if any(float(ln.discount or 0) > 0 for ln in lines):
        return {}

    gross_by_line = {
        ln.line_number: Decimal(str(ln.unit_price or 0))
        * Decimal(str(ln.quantity_ordered or ln.units_ordered or 0))
        for ln in lines
    }
    total_gross = sum(gross_by_line.values())
    if total_gross <= 0:
        return {}
    # A header discount larger than the order itself is bad data, not a 100%
    # discount; capping keeps a line from going negative.
    if header_discount > total_gross:
        header_discount = total_gross

    allocated: dict[int, Decimal] = {}
    for line_number, gross in gross_by_line.items():
        allocated[line_number] = (header_discount * gross / total_gross).quantize(
            Decimal("0.00001"), ROUND_HALF_UP
        )

    remainder = header_discount - sum(allocated.values())
    if remainder and allocated:
        biggest = max(gross_by_line, key=lambda k: gross_by_line[k])
        allocated[biggest] += remainder

    return {k: float(v) for k, v in allocated.items() if v > 0}


def _normalize_tax_row(row: dict) -> dict:
    """Accept either stored spelling of a line tax and return the canonical one.

    Manual orders used to persist the REQUEST shape (`code` / `rate` /
    `rate_code`) while imported orders persisted the canonical
    `ProductTaxDTO` dump (`tax_type_id` / `tax_rate: {...}`). New writes are all
    canonical — `canonical_line_dtos` sees to that — but rows written before it
    are still in the database, and a reprocess or backfill has to be able to
    read them or the very orders that most need repairing are the ones it skips.
    """
    if "tax_type_id" in row:
        return row

    normalized: dict = {"tax_type_id": row.get("code") or "01"}
    if row.get("rate") is not None:
        normalized["tax_rate"] = {
            "id": str(row.get("rate_code") or "0"),
            "percentage": row.get("rate"),
            "code": row.get("rate_code"),
        }
    if row.get("other_tax_type") is not None:
        normalized["other_tax_type"] = row["other_tax_type"]
    if row.get("special_fields") is not None:
        normalized["special_fields"] = row["special_fields"]
    if row.get("amount") is not None:
        normalized["amount"] = row["amount"]
        normalized["is_amount"] = row.get("rate") is None
    return normalized


def _normalize_discount_row(row: dict) -> dict:
    """The discount counterpart of `_normalize_tax_row`."""
    if "discount_type_id" in row:
        return row
    return {
        "discount_type_id": row.get("code") or "99",
        "reason": row.get("nature"),
        "percentage": row.get("percentage"),
        "amount": row.get("amount"),
        "is_amount": row.get("percentage") is None and row.get("amount") is not None,
    }


def _line_input_from_structured(line) -> LineInput:
    """`LineInput` for a line that carries structured taxes/discounts JSONB.

    One builder for every caller — the imported path, the reprocess path and the
    backfill all have to produce the SAME numbers, and each having its own
    translation from JSONB to DTO is how they stopped agreeing before.

    Reads the canonical stored shape so nothing is re-derived: the discount
    natures, rates and special fields are taken as written, and only the
    arithmetic is redone. Legacy rows are normalized on the way in.
    """
    quantity = Decimal(str(line.quantity_ordered or line.units_ordered or 0))
    net_price = Decimal(str(line.net_price if line.net_price is not None else (line.unit_price or 0)))

    return LineInput(
        price=net_price,
        quantity=quantity,
        is_packaged=True,
        # An excise priced per unit multiplies by the ORDER quantity, not by 1.
        detail_quantity=quantity or Decimal("1"),
        discounts=[
            ProductDiscountDTO(**_normalize_discount_row(d))
            for d in (line.discounts or [])
        ],
        taxes=[ProductTaxDTO(**_normalize_tax_row(t)) for t in (line.taxes or [])],
    )


def _recompute_imported_line(line, product=None) -> None:
    """Recompute one order line's money from its own fiscal detail, in place.

    `discount`, `tax` and `line_total` on an imported line used to be whatever
    the spreadsheet said, with no structure behind them — which meant an order
    could not be billed without re-deriving the tax from scratch at invoice
    time, on numbers that had never been checked against each other.

    Now the line carries the full breakdown (the product's taxes, the discount
    as 07 Comercial) and this runs the SAME `LineCalculator` a sale runs, over
    the ORDER quantity. A pedido and the factura it becomes therefore agree by
    construction rather than by coincidence.

    A line with no structured detail is left exactly as the spreadsheet had it:
    there is nothing to derive a tax from, and inventing a rate would be worse
    than carrying the customer's own figure.
    """
    if not (line.taxes or line.discounts):
        return

    computed = LineCalculator().compute(
        _line_input_from_structured(line),
        cabys_code=line.cabys or (product.cabys.code if product and product.cabys else None),
    )
    line.discount = _round_money(computed.discount.total_discount_amount)
    line.tax = _round_money(computed.tax.net_tax)
    line.line_total = _round_money(computed.subtotal + computed.tax.net_tax)


def _resum_order_totals(order: Order) -> None:
    """Re-add the order's totals from its lines.

    The header figures the spreadsheet carries are the chain's, and once the
    lines have been recomputed they are the only numbers that reconcile. Summed
    here rather than trusted so `grand_total` always equals what the lines say —
    the invoice is built from the lines, and a header that disagrees with them
    is a discrepancy the user only discovers at Hacienda.
    """
    lines = list(order.lines or [])
    if not lines:
        return

    gross = sum(
        Decimal(str(ln.unit_price or 0))
        * Decimal(str(ln.quantity_ordered or ln.units_ordered or 0))
        for ln in lines
    )
    discounts = sum(Decimal(str(ln.discount or 0)) for ln in lines)
    taxes = sum(Decimal(str(ln.tax or 0)) for ln in lines)

    order.subtotal = _round_money(gross)
    order.discounts = _round_money(discounts)
    order.net_total = _round_money(gross - discounts)
    order.taxes = _round_money(taxes)
    order.grand_total = _round_money(gross - discounts + taxes)
    order.line_count = len(lines)
    order.total_quantities = sum(
        int(ln.quantity_ordered or ln.units_ordered or 0) for ln in lines
    )


def _rebuild_imported_lines(
    order: Order,
    parsed,
    organization_id: str,
    product_repo: ProductRepository,
) -> None:
    """Replace an order's lines from a parsed spreadsheet, fully costed.

    An imported line is rebuilt into the same shape a POS-captured one has —
    CABYS, net price, structured taxes, structured discounts — so the pedido can
    be billed later without re-deriving anything, and so the totals shown on it
    are the ones the invoice will carry. The spreadsheet supplies the quantities
    and the negotiated price; the PRODUCT supplies the fiscal configuration,
    because that is where the org maintains it.

    Shared by the first import and by every reprocess. They each had their own
    copy of this loop and the copies had already diverged — one carried the
    product's taxes, the other did not — so an order's fiscal detail depended on
    whether anyone had happened to reprocess it.
    """
    allocated_discounts = _allocate_header_discount(parsed)

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
        # The line's own discount wins; the header allocation only fills in for
        # a spreadsheet that left every line at zero — see
        # `_allocate_header_discount`.
        discount_amount = float(ln.discount or 0) or allocated_discounts.get(
            ln.line_number, 0.0
        )

        line = OrderLine(
            line_number=ln.line_number,
            quantity_ordered=ln.quantity_ordered,
            units_ordered=ln.units_ordered,
            unit_price=ln.unit_price,
            discount=discount_amount,
            line_total=ln.line_total,
            tax=ln.tax,
            quantity_dispatched=ln.quantity_dispatched,
            dispatch_rejection_reason=ln.dispatch_rejection_reason,
            quantity_received=ln.quantity_received,
            article_code=ln.article_code,
            product_id=product.id,
            description=ln.description,
            cabys=(product.cabys.code if product.cabys else None),
            net_price=_imported_line_net_price(ln, product),
            taxes=_imported_line_taxes(product),
            discounts=_imported_line_discounts(discount_amount),
        )
        _recompute_imported_line(line, product)
        order.lines.append(line)

    _resum_order_totals(order)


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
            gln=parsed.dispatch_gln or None,
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

    _rebuild_imported_lines(order, parsed, organization_id, product_repo)


def _update_order_from_parsed(order: Order, parsed) -> None:
    """Update order entity fields from a parsed result.

    Lines are handled by `_upsert_order_entities`. The money totals written here
    are the spreadsheet's, and they are immediately superseded by
    `_resum_order_totals`, which re-adds them from the recomputed lines — see
    the call site. They are still assigned first so an order whose lines carry
    no fiscal detail at all keeps the chain's own figures.
    """
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


def _generate_crossdocking_outputs(order: Order, color=None) -> None:
    """Generate crossdocking PDF and NuevoReporte Excel for an order."""
    resolved_color = color or order.report_color or _default_color_for_order(order)
    crossdocking_data = build_crossdocking_data(order)
    try:
        cd_pdf_url = create_crossdocking_pdf(order, crossdocking_data, resolved_color)
        order.crossdocking_pdf_url = cd_pdf_url
        logger.info(f"Crossdocking PDF generated: {cd_pdf_url}")
    except Exception as e:
        logger.warning(f"Crossdocking PDF generation failed: {e}")

    try:
        nr_url = create_nuevo_reporte(order, crossdocking_data, resolved_color)
        order.nuevo_reporte_url = nr_url
        logger.info(f"NuevoReporte generated: {nr_url}")
    except Exception as e:
        logger.warning(f"NuevoReporte generation failed: {e}")


# ─── Manual orders / pedidos manuales (TSR-152) ─────────────────────────────

#: Statuses a manual order may open in. A proforma is an order in an early
#: status, NOT a separate document type — see docs/MANUAL_ORDERS.md.
_QUOTE_STATUS = "quote"
_PENDING_STATUS = "pending"

#: Cross-docking uses order_type '73'. A manual order must never collide with
#: it, or it would be pulled into a flow that expects sale points and bultos.
_CROSSDOCKING_ORDER_TYPE = "73"


def _round_money(value) -> float:
    """Money is stored at 5 dp but reconciles at 2 — round once, at the edge."""
    return float(Decimal(str(value or 0)).quantize(Decimal("0.00001"), ROUND_HALF_UP))


def _generate_manual_document_number(repo: OrderRepository, organization_id: str) -> str:
    """Next free `PM-000123` for this organization.

    Prefixed so a hand-captured pedido is distinguishable at a glance from an
    imported one, and scanned forward rather than counted, because imported
    orders share the same table and the same uniqueness constraint.
    """
    existing = repo.session.execute(
        text(
            "SELECT document_number FROM crossdocking_orders "
            "WHERE company_id = :org AND document_number LIKE 'PM-%' "
            "ORDER BY document_number DESC LIMIT 1"
        ),
        {"org": organization_id},
    ).scalar()

    next_seq = 1
    if existing:
        try:
            next_seq = int(str(existing).split("-", 1)[1]) + 1
        except (IndexError, ValueError):
            # A hand-typed "PM-foo" must not wedge the sequence.
            next_seq = 1

    for _ in range(50):
        candidate = f"PM-{next_seq:06d}"
        if not repo.find_by_company_and_document(organization_id, candidate):
            return candidate
        next_seq += 1

    raise ValueError("Could not allocate a manual order number")


def canonical_line_dtos(line) -> tuple[list[ProductDiscountDTO], list[ProductTaxDTO]]:
    """Translate a manual-order line's taxes/discounts into the CANONICAL shape.

    There is one storage shape for `order_line.taxes` / `.discounts` across the
    whole module — the `ProductTaxDTO` / `ProductDiscountDTO` dump, which is
    also what the product catalog stores, what the FE line detail sends and what
    the invoice reads. The manual-order request DTO has its own flatter spelling
    (`code`/`rate`/`nature`), and persisting THAT verbatim meant a POS-captured
    pedido and an imported one carried the same column in two different shapes:
    nothing could read both, and `ProductTaxDTO(**row)` raised on one of them.

    So the request shape is translated once, here, and the canonical DTOs are
    used for BOTH the arithmetic and the persisted JSONB.
    """
    discounts = [
        ProductDiscountDTO(
            discount_type_id=d.code or "99",
            # Nota 20 requires a nature for code 99; the FE collects it, and
            # the calculator rejects the line without it.
            reason=d.nature,
            percentage=d.percentage,
            is_amount=d.percentage is None and d.amount is not None,
            amount=d.amount,
        )
        for d in (line.discounts or [])
    ]

    taxes = []
    for t in (line.taxes or []):
        sf = getattr(t, "special_fields", None)
        taxes.append(
            ProductTaxDTO(
                tax_type_id=t.code or "01",
                tax_rate=(
                    TaxRateDTO(percentage=t.rate, code=t.rate_code)
                    if t.rate is not None
                    else None
                ),
                tax_factor=(
                    TaxFactorDTO(id=str(t.rate_code or "factor"), factor=t.factor)
                    if getattr(t, "factor", None) is not None
                    else None
                ),
                other_tax_type=getattr(t, "other_tax_type", None),
                special_fields=(
                    TaxSpecialFieldsDTO(
                        quantity=sf.quantity,
                        percentage=sf.percentage,
                        proportion=sf.proportion,
                        volume_consumption=sf.volume_consumption,
                        tax_amount=(
                            TaxAmountDTO(
                                id=str(sf.tax_amount_id or "0"),
                                amount=sf.tax_unit_amount,
                            )
                            if sf.tax_unit_amount is not None
                            or sf.tax_amount_id is not None
                            else None
                        ),
                    )
                    if sf is not None
                    else None
                ),
                is_amount=t.rate is None and t.amount is not None,
                amount=t.amount,
            )
        )

    return discounts, taxes


def _line_amounts(line) -> tuple[float, float, float, float]:
    """Authoritative (subtotal, discount, tax, line_total) for one line.

    When the line carries a STRUCTURED tax/discount breakdown we recompute it
    through the same `LineCalculator` a sale uses, so a pedido and the factura
    it later becomes agree. When it carries only flat amounts we recompute the
    arithmetic but take the caller's tax figure, because there is nothing to
    derive it from.

    Either way the ORDER totals are summed from these values and never read from
    the request body.
    """
    gross = Decimal(str(line.unit_price or 0)) * Decimal(str(line.quantity or 0))

    if line.taxes or line.discounts:
        discount_dtos, tax_dtos = canonical_line_dtos(line)
        computed = LineCalculator().compute(
            LineInput(
                price=Decimal(str(line.unit_price or 0)),
                quantity=Decimal(str(line.quantity or 0)),
                is_packaged=True,
                # A per-unit excise multiplies by the line quantity, not by 1.
                detail_quantity=Decimal(str(line.quantity or 1)),
                discounts=discount_dtos,
                taxes=tax_dtos,
            ),
            cabys_code=line.cabys,
        )
        subtotal = computed.subtotal
        discount = computed.discount.total_discount_amount
        tax = computed.tax.net_tax
        return (
            _round_money(subtotal),
            _round_money(discount),
            _round_money(tax),
            _round_money(subtotal + tax),
        )

    discount = Decimal(str(line.discount or 0))
    tax = Decimal(str(line.tax or 0))
    subtotal = gross - discount
    return (
        _round_money(subtotal),
        _round_money(discount),
        _round_money(tax),
        _round_money(subtotal + tax),
    )


def create_manual_order(
    organization_id: str,
    dto: CreateManualOrderDTO,
    created_by: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> OrderResponse:
    """Create a pedido captured by hand in the POS document editor.

    Contract: docs/MANUAL_ORDERS.md §9. The rules that matter:

    1. Totals in the body are a HINT. Everything is recomputed here.
    2. `document_number` may be user-supplied; a collision is a 409, not a
       silent overwrite.
    3. `Idempotency-Key` is honoured, because a pedido captured offline is
       replayed from the outbox and must not become two orders.
    4. `order_type` never becomes '73' — that is cross-docking.
    """
    with OrderRepository() as repo:
        # ── Idempotent replay ────────────────────────────────────────────
        if idempotency_key:
            existing = repo.session.execute(
                select(Order).where(
                    Order.company_id == organization_id,
                    Order.idempotency_key == idempotency_key,
                )
            ).scalars().first()
            if existing:
                return order_to_response(existing)

        client_repo = ClientRepository.from_session(repo.session)
        store_repo = StoreRepository.from_session(repo.session)
        dept_repo = DepartmentRepository.from_session(repo.session)

        client = None
        if dto.client_id:
            client = client_repo.find_by_id_and_company(
                uuid.UUID(dto.client_id), organization_id
            )
            if not client:
                raise LookupError(f"Client '{dto.client_id}' not found")

        # ── Delivery target ──────────────────────────────────────────────
        loc = dto.delivery_location
        store = None
        if loc and loc.mode == "store" and loc.store_id:
            store = store_repo.find_by_id_and_company(
                uuid.UUID(loc.store_id), organization_id
            )
            if not store:
                raise LookupError(f"Store '{loc.store_id}' not found")
            if client and store.client_id != client.client_id:
                raise ValueError("Delivery point does not belong to the selected client")

        has_address = bool(loc and (loc.address or loc.state_id))
        if not store and not has_address:
            # The free-text blob that used to satisfy this is gone on purpose.
            raise ValueError("A delivery point or an address is required")

        department = None
        if dto.department_id:
            department = dept_repo.find_by_id_and_company(
                uuid.UUID(dto.department_id), organization_id
            )
            if not department:
                raise LookupError(f"Department '{dto.department_id}' not found")
            if client and department.client_id != client.client_id:
                raise ValueError("Department does not belong to the selected client")

        # ── Document number ──────────────────────────────────────────────
        if dto.document_number and dto.document_number.strip():
            document_number = dto.document_number.strip()
            if repo.find_by_company_and_document(organization_id, document_number):
                raise FileExistsError(
                    f"Order '{document_number}' already exists for this organization"
                )
        else:
            document_number = _generate_manual_document_number(repo, organization_id)

        order_type = dto.order_type or "manual"
        if order_type == _CROSSDOCKING_ORDER_TYPE:
            raise ValueError("order_type '73' is reserved for cross-docking")

        order = Order(
            company_id=organization_id,
            document_number=document_number,
            source="manual",
            document_type=dto.document_type or "PM",
            order_type=order_type,
            order_status=_QUOTE_STATUS if dto.is_quote else _PENDING_STATUS,
            creation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            delivery_date=dto.delivery_date,
            created_by=created_by,
            idempotency_key=idempotency_key,
            client_id=client.client_id if client else None,
            deliver_to_store_id=store.store_id if store else None,
            department_id=department.department_id if department else None,
            delivery_location_name=(loc.name if loc else None),
            # `receiver` / `custom` modes reuse the storefront pedido's columns
            # rather than inventing a second address shape.
            state_id=(loc.state_id if loc else None),
            county_id=(loc.county_id if loc else None),
            district_id=(loc.district_id if loc else None),
            neighborhood_id=(loc.neighborhood_id if loc else None),
            delivery_address=(loc.address if loc else None),
            activity_code=dto.activity_code,
            sale_condition=dto.sale_condition,
            credit_term=dto.credit_term,
            currency_code=dto.currency_code,
            exchange_rate=dto.exchange_rate,
            assignment_id=dto.assignment_id,
            branch_number=dto.branch_number,
            terminal_number=dto.terminal_number,
            payments=[p.model_dump() for p in dto.payments] if dto.payments else [],
            event=dto.event,
            comment=dto.comment,
            asset_id=uuid.UUID(dto.asset_id) if dto.asset_id else None,
            odometer=dto.odometer,
            reported_issue=dto.reported_issue,
        )

        # ── Lines + authoritative totals ─────────────────────────────────
        subtotal = Decimal("0")
        discounts = Decimal("0")
        taxes = Decimal("0")
        quantities = Decimal("0")

        for line in dto.lines:
            line_subtotal, line_discount, line_tax, line_total = _line_amounts(line)
            line_discount_dtos, line_tax_dtos = canonical_line_dtos(line)
            subtotal += Decimal(str(line_subtotal)) + Decimal(str(line_discount))
            discounts += Decimal(str(line_discount))
            taxes += Decimal(str(line_tax))
            quantities += Decimal(str(line.quantity or 0))

            order.lines.append(
                OrderLine(
                    line_number=line.line_number,
                    product_id=line.product_id,
                    description=line.description,
                    article_code=line.internal_code,
                    quantity_ordered=int(line.quantity or 0),
                    units_ordered=int(line.quantity or 0),
                    unit_price=line.unit_price,
                    net_price=line.unit_price,
                    discount=line_discount,
                    tax=line_tax,
                    line_total=line_total,
                    cabys=line.cabys,
                    # Stored in the canonical shape, NOT the request's — see
                    # `canonical_line_dtos`. One shape per column is what lets
                    # reprocess, backfill and billing read every order's lines.
                    taxes=([t.model_dump() for t in line_tax_dtos] or None),
                    discounts=([d.model_dump() for d in line_discount_dtos] or None),
                )
            )

        order.subtotal = _round_money(subtotal)
        order.discounts = _round_money(discounts)
        order.net_total = _round_money(subtotal - discounts)
        order.taxes = _round_money(taxes)
        order.grand_total = _round_money(subtotal - discounts + taxes)
        order.total_quantities = int(quantities)
        order.line_count = len(order.lines)

        if dto.totals and abs(float(order.grand_total) - float(dto.totals.grand_total)) > 0.01:
            logger.warning(
                "Manual order %s: client total %.5f != server total %.5f — server wins",
                document_number,
                dto.totals.grand_total,
                order.grand_total,
            )

        order = repo.save(order)
        return order_to_response(order)


def generate_order_ticket(organization_id: str, document_number: str) -> OrderResponse:
    """Render (or re-render) the order's 80mm ticket and return the order.

    On demand rather than at creation: most orders are never printed, and
    rendering a PDF per order would spend Lambda time on paper nobody asks for.
    Re-rendering is deliberate too — a ticket reprinted after the order was
    invoiced should show the consecutive and QR it did not have before.
    """
    from app.services.ticket_service import create_order_ticket

    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(f"Order '{document_number}' not found")

        order.ticket_url = create_order_ticket(order)
        order = repo.save(order)
        return order_to_response(order)


def link_order_invoice(
    organization_id: str,
    document_number: str,
    sale_id: str,
    document_type: Optional[str] = None,
    consecutive_number: Optional[str] = None,
    document_key: Optional[str] = None,
    issued_on: Optional[str] = None,
) -> OrderResponse:
    """Record that a delivered order was billed.

    Without this the frontend cannot know a pedido is already invoiced, and
    nothing stops a second factura being issued for the same order.
    """
    with OrderRepository() as repo:
        order = repo.find_by_company_and_document(organization_id, document_number)
        if not order:
            raise LookupError(f"Order '{document_number}' not found")

        if order.invoice_sale_id and order.invoice_sale_id != sale_id:
            raise FileExistsError(
                f"Order '{document_number}' is already invoiced as "
                f"{order.invoice_consecutive_number or order.invoice_sale_id}"
            )

        order.invoice_sale_id = sale_id
        order.invoice_document_type = document_type
        order.invoice_consecutive_number = consecutive_number
        order.invoice_document_key = document_key
        order.invoice_issued_on = issued_on or datetime.now(timezone.utc).isoformat()

        order = repo.save(order)
        return order_to_response(order)
