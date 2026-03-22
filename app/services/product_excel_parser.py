from __future__ import annotations

from io import BytesIO
from typing import Any

import openpyxl

from app.exceptions import ExcelParsingException

EXPECTED_HEADERS = [
    "COD_ARTIC",
    "COD_BARRA",
    "COD_INTERNO",
    "DESCRIPCION",
    "CANTIDAD_CAJA",
    "UNIDAD_MEDIDA",
    "PRECIO",
    "CATEGORIA",
]


def _safe_int(value) -> int:
    """Convert value to int, returning 0 if conversion fails."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _safe_str(value) -> str:
    """Convert value to string, returning empty string if None."""
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value) -> float:
    """Convert value to float, returning 0.0 if conversion fails."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def parse_product_file(file: BytesIO) -> list[dict[str, Any]]:
    """
    Parse Excel file and return list of product data dictionaries.

    Args:
        file: BytesIO object containing Excel file data

    Returns:
        List of dictionaries with keys:
        - cod_artic: str
        - cod_barra: str
        - cod_interno: str
        - descripcion: str
        - cantidad_caja: int
        - unidad_medida: str
        - precio: float (ignored for creates/updates)
        - categoria: str

    Raises:
        ExcelParsingException: If file is invalid or headers are missing
    """
    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        raise ExcelParsingException(f"Could not open Excel file: {e}")

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 1:
        raise ExcelParsingException("File must have at least a header row")

    # Validate headers
    raw_headers = [_safe_str(h) for h in rows[0]]
    
    # Check for missing headers
    missing_headers = []
    for expected in EXPECTED_HEADERS:
        if expected not in raw_headers:
            missing_headers.append(expected)
    
    if missing_headers:
        raise ExcelParsingException(
            f"Missing required headers: {', '.join(missing_headers)}"
        )

    # Create header index mapping
    header_indices = {header: raw_headers.index(header) for header in EXPECTED_HEADERS}

    # Parse data rows
    products = []
    data_rows = rows[1:]

    for row in data_rows:
        # Skip empty rows
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        # Extract values using header indices
        product_data = {
            "cod_artic": _safe_str(row[header_indices["COD_ARTIC"]] if len(row) > header_indices["COD_ARTIC"] else None),
            "cod_barra": _safe_str(row[header_indices["COD_BARRA"]] if len(row) > header_indices["COD_BARRA"] else None),
            "cod_interno": _safe_str(row[header_indices["COD_INTERNO"]] if len(row) > header_indices["COD_INTERNO"] else None),
            "descripcion": _safe_str(row[header_indices["DESCRIPCION"]] if len(row) > header_indices["DESCRIPCION"] else None),
            "cantidad_caja": _safe_int(row[header_indices["CANTIDAD_CAJA"]] if len(row) > header_indices["CANTIDAD_CAJA"] else None),
            "unidad_medida": _safe_str(row[header_indices["UNIDAD_MEDIDA"]] if len(row) > header_indices["UNIDAD_MEDIDA"] else None),
            "precio": _safe_float(row[header_indices["PRECIO"]] if len(row) > header_indices["PRECIO"] else None),
            "categoria": _safe_str(row[header_indices["CATEGORIA"]] if len(row) > header_indices["CATEGORIA"] else None),
        }

        products.append(product_data)

    return products
