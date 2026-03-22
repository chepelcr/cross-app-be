from typing import Optional

from pydantic import BaseModel, Field

from app.enums.report_color import ReportColorScheme


class SelectColorDTO(BaseModel):
    """Request body for selecting a report color scheme (used in reprocess)."""

    color: Optional[ReportColorScheme] = Field(
        None,
        description=(
            "Color scheme for the generated reports (green, orange, blue, green_alt). "
            "If not provided, retains the stored color for this order."
        ),
    )

    model_config = {"populate_by_name": True}
