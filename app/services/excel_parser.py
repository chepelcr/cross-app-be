from __future__ import annotations

from collections import OrderedDict
from io import BytesIO

import openpyxl

from app.exceptions import ExcelParsingException
from app.dtos.responses.crossdocking_dto import (
    CrossDockingData,
    ItemResponse,
    SalePointResponse,
)
from app.utils.crossdocking_utils import build_summaries

EXPECTED_HEADERS = [
    "NUM_DOC",
    "NOMBRE_CLIENTE",
    "FECHA_DOC",
    "FECHA_ENTREGA",
    "NOMBRE_DESPACHO",
    "COD_INTERNO",
    "COD_ARTIC_ORI",
    "DESCRIPCION",
    "CANTIDAD",
    "UXC",
    "CANTIDADES",
    "FALTANTES",
]


def _safe_int(value) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _safe_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_description(descripcion: str) -> tuple[str, int | None]:
    if " :: " in descripcion:
        parts = descripcion.rsplit(" :: ", maxsplit=1)
        name = parts[0].strip()
        try:
            units = int(parts[1].strip())
        except (ValueError, TypeError):
            return name, None
        return name, units
    return descripcion.strip(), None


def _parse_sale_point_name(nombre_despacho: str) -> tuple[str, str]:
    parts = nombre_despacho.strip().split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return parts[0], ""


class CrossDockingParseResult:
    """Intermediate result holding both the crossdocking data and the order metadata."""

    def __init__(
        self,
        document_number: str,
        client_name: str,
        document_date: str,
        delivery_date: str,
        crossdocking: CrossDockingData,
    ):
        self.document_number = document_number
        self.client_name = client_name
        self.document_date = document_date
        self.delivery_date = delivery_date
        self.crossdocking = crossdocking


def parse_crossdocking_file(file: BytesIO) -> CrossDockingParseResult:
    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        raise ExcelParsingException(f"Could not open Excel file: {e}")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        raise ExcelParsingException("File must have at least a header row and a metadata row")

    raw_headers = [_safe_str(h) for h in rows[0]]

    # Detect column offset: some files have extra leading columns (e.g. "Tipo Doc")
    col_offset = 0
    for offset in range(min(3, len(raw_headers))):
        if raw_headers[offset] == EXPECTED_HEADERS[0]:
            col_offset = offset
            break

    headers = raw_headers[col_offset:]
    for i, expected in enumerate(EXPECTED_HEADERS):
        if i >= len(headers) or headers[i] != expected:
            raise ExcelParsingException(
                f"Expected header '{expected}' in column {chr(65 + i + col_offset)}, "
                f"got '{headers[i] if i < len(headers) else '(missing)'}'"
            )

    # Strip leading columns from all rows if offset detected
    if col_offset > 0:
        rows = [row[col_offset:] for row in rows]

    # Check if row 2 has order metadata (NUM_DOC populated) or starts with item data directly
    meta_row = rows[1]
    document_number = _safe_str(meta_row[0])
    client_name = _safe_str(meta_row[1])
    document_date = _safe_str(meta_row[2])
    delivery_date = _safe_str(meta_row[3])

    if document_number:
        data_rows = rows[2:]
    else:
        # No metadata row — all rows after header are item data
        document_number = ""
        client_name = ""
        document_date = ""
        delivery_date = ""
        data_rows = rows[1:]

    # Parse line items
    sale_points_map: OrderedDict[str, list[ItemResponse]] = OrderedDict()

    for row in data_rows:
        nombre_despacho = _safe_str(row[4]) if len(row) > 4 else ""
        if not nombre_despacho:
            continue

        cod_interno = _safe_str(row[5]) if len(row) > 5 else ""
        cod_artic_ori = _safe_str(row[6]) if len(row) > 6 else ""
        descripcion_raw = _safe_str(row[7]) if len(row) > 7 else ""
        cantidad = _safe_int(row[8]) if len(row) > 8 else 0
        uxc = _safe_int(row[9]) if len(row) > 9 else 0
        enviados = _safe_int(row[10]) if len(row) > 10 else 0

        description, parsed_uxc = _parse_description(descripcion_raw)
        units_per_box = parsed_uxc if parsed_uxc is not None else uxc

        item = ItemResponse(
            internal_code=cod_interno,
            original_code=cod_artic_ori,
            description=description,
            quantity=cantidad,
            units_per_box=units_per_box,
            total_units=cantidad * units_per_box,
            sent=enviados,
            missing=cantidad - enviados,
        )

        if nombre_despacho not in sale_points_map:
            sale_points_map[nombre_despacho] = []
        sale_points_map[nombre_despacho].append(item)

    sale_points: list[SalePointResponse] = []
    for full_name, items in sale_points_map.items():
        store_number, store_name = _parse_sale_point_name(full_name)
        sale_points.append(
            SalePointResponse(
                store_number=store_number,
                store_name=store_name,
                full_name=full_name,
                items=items,
                total_boxes=sum(it.sent for it in items),
                total_units=sum(it.sent * it.units_per_box for it in items),
            )
        )

    item_summary, box_summary, totals = build_summaries(sale_points)

    crossdocking = CrossDockingData(
        sale_points=sale_points,
        item_summary=item_summary,
        box_summary=box_summary,
        totals=totals,
    )

    return CrossDockingParseResult(
        document_number=document_number,
        client_name=client_name,
        document_date=document_date,
        delivery_date=delivery_date,
        crossdocking=crossdocking,
    )
