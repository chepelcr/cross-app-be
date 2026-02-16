import logging
from io import BytesIO
from typing import Dict, List

import openpyxl

from app.dtos import ExcelFileDTO
from app.models.store_slot import StoreSlot
from app.repositories.store_slot_repository import StoreSlotRepository
from app.utils.crossdocking_utils import decode_excel_file

logger = logging.getLogger(__name__)


def parse_store_slots_excel(file: BytesIO) -> List[StoreSlot]:
    """Parse PUNTOS DE VENTA Excel sheet into StoreSlot list.

    Expected columns: Codigo | Nombre | SLOT ID | Cadena
    """
    wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        raise ValueError("File must have at least a header row and data")

    slots = []
    for row in rows[1:]:
        code = str(row[0]).strip() if row[0] else ""
        if not code:
            continue
        slots.append(
            StoreSlot(
                store_code=code,
                store_name=str(row[1]).strip() if len(row) > 1 and row[1] else "",
                slot_id=str(row[2]).strip() if len(row) > 2 and row[2] else "",
                chain=str(row[3]).strip() if len(row) > 3 and row[3] else "",
            )
        )
    return slots


def upload_store_slots(body: ExcelFileDTO) -> int:
    """Upload store slots from an Excel file. Returns count of upserted records."""
    file = decode_excel_file(body)
    slots = parse_store_slots_excel(file)
    with StoreSlotRepository() as repo:
        return repo.bulk_upsert(slots)


def get_slot_map() -> Dict[str, str]:
    """Get store_code -> slot_id mapping."""
    with StoreSlotRepository() as repo:
        return repo.get_slot_map()
