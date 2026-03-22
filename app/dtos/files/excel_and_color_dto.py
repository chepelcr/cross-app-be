from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.dtos.files.excel_dto import ExcelDTO
from app.enums.report_color import ReportColorScheme


class ExcelAndColorDTO(ExcelDTO):
    """DTO for Excel file uploads with optional color scheme for report generation."""

    color: Optional[ReportColorScheme] = Field(
        None,
        description="Color scheme for generated reports (green, orange, blue, green_alt). Defaults to green.",
    )
