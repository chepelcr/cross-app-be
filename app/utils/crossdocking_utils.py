from __future__ import annotations

import base64
from collections import OrderedDict
from io import BytesIO
from typing import TYPE_CHECKING

from app.dtos.files import ExcelDTO
from app.dtos.responses.crossdocking_dto import (
    BoxSummary,
    CrossDockingTotals,
    ItemSummary,
    SalePointResponse,
)

if TYPE_CHECKING:
    pass


def build_summaries(
    sale_points: list[SalePointResponse],
) -> tuple[list[ItemSummary], list[BoxSummary], CrossDockingTotals]:
    """Build item summary, box summary, and totals from a list of sale points."""
    # Item summary: aggregate sent quantities per product
    item_agg: OrderedDict[str, dict] = OrderedDict()
    for sp in sale_points:
        for it in sp.items:
            key = it.internal_code
            if key not in item_agg:
                item_agg[key] = {
                    "internal_code": it.internal_code,
                    "original_code": it.original_code,
                    "description": it.description,
                    "units_per_box": it.units_per_box,
                    "total_boxes": 0,
                }
            item_agg[key]["total_boxes"] += it.sent

    item_summary = [
        ItemSummary(
            internal_code=v["internal_code"],
            original_code=v["original_code"],
            description=v["description"],
            units_per_box=v["units_per_box"],
            total_boxes=v["total_boxes"],
            total_units=v["total_boxes"] * v["units_per_box"],
        )
        for v in item_agg.values()
    ]

    # Box summary: group sale points by total sent units
    box_agg: OrderedDict[int, dict] = OrderedDict()
    for sp in sale_points:
        num_items = sp.total_boxes
        if num_items not in box_agg:
            box_agg[num_items] = {"count": 0, "total_boxes": 0, "total_units": 0}
        box_agg[num_items]["count"] += 1
        box_agg[num_items]["total_boxes"] += sp.total_boxes
        box_agg[num_items]["total_units"] += sp.total_units

    box_summary = [
        BoxSummary(
            items_per_box=items_count,
            box_count=agg["count"],
            total_boxes=agg["total_boxes"],
            total_units=agg["total_units"],
        )
        for items_count, agg in sorted(box_agg.items())
    ]

    total_boxes = sum(sp.total_boxes for sp in sale_points)
    total_units = sum(sp.total_units for sp in sale_points)
    total_line_items = sum(len(sp.items) for sp in sale_points)

    totals = CrossDockingTotals(
        total_sale_points=len(sale_points),
        total_line_items=total_line_items,
        total_boxes=total_boxes,
        total_units=total_units,
    )

    return item_summary, box_summary, totals


def decode_excel_file(body: ExcelDTO) -> BytesIO:
    """Decode a Base64-encoded Excel file from an ExcelDTO into a BytesIO stream."""
    if not body.data:
        raise ValueError("File data is required")

    try:
        file_data = body.data
        if ";base64," in file_data:
            file_data = file_data.split(";base64,", 1)[1]
        decoded = base64.b64decode(file_data)
    except Exception:
        raise ValueError("Invalid Base64 data")

    return BytesIO(decoded)
