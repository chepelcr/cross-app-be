"""Boundary DTO for product Excel imports.

The Excel parser hands back a list of dicts whose keys come from the
EXPECTED_HEADERS catalog (`cod_artic`, `cod_barra`, ...). Wrapping at the
service boundary into this DTO kills the downstream `row.get(...)` smell.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductExcelRowDTO(BaseModel):
    """Single normalized row from the imported Excel sheet."""

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    cod_artic: Optional[str] = Field(default=None)
    cod_barra: Optional[str] = Field(default=None)
    cod_interno: Optional[str] = Field(default=None)
    descripcion: Optional[str] = Field(default=None)
    cantidad_caja: Optional[int] = Field(default=None)
    unidad_medida: Optional[str] = Field(default=None)
    precio: Optional[float] = Field(default=None)
    categoria: Optional[str] = Field(default=None)

    @field_validator(
        "cod_artic", "cod_barra", "cod_interno", "descripcion", "unidad_medida", "categoria",
        mode="before",
    )
    @classmethod
    def _coerce_text(cls, value):
        # Excel libs hand back ints/floats for some text columns; force str
        # before strip_whitespace runs. None stays None.
        if value is None:
            return None
        return str(value)
