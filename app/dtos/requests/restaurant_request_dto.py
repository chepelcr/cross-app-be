from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ComboItemDTO(BaseModel):
    """One component of a combo."""

    model_config = ConfigDict(populate_by_name=True)

    product_id: str = Field(..., min_length=1)
    quantity: float = Field(default=1, gt=0)
    sort_order: int = Field(default=0, ge=0)


class ComboUpsertDTO(BaseModel):
    """Replace a combo's component set.

    The combo's PRICE stays on the product row — a combo is priced as itself,
    not as the sum of its parts. These components exist so the POS can explode
    the line and keep each part's own CABYS and IVA rate.
    """

    model_config = ConfigDict(populate_by_name=True)

    items: List[ComboItemDTO] = Field(..., min_length=1)


class ModifierDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100)
    price_delta: float = Field(default=0)
    #: Linking a real product makes this modifier its OWN cart line, so its
    #: CABYS and IVA rate are its own rather than the parent's.
    product_id: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)


class ModifierGroupCreateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100)
    min_select: int = Field(default=0, ge=0)
    max_select: Optional[int] = Field(default=None, ge=1)
    required: bool = False
    sort_order: int = Field(default=0, ge=0)
    modifiers: List[ModifierDTO] = Field(default_factory=list)

    @model_validator(mode="after")
    def _bounds_make_sense(self) -> "ModifierGroupCreateDTO":
        if self.max_select is not None and self.max_select < self.min_select:
            raise ValueError("max_select cannot be lower than min_select")
        if self.required and self.min_select == 0:
            # "Required" with a floor of zero is a contradiction the cashier
            # would hit as an un-dismissable prompt.
            self.min_select = 1
        return self


class ModifierGroupUpdateDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(None, max_length=100)
    min_select: Optional[int] = Field(None, ge=0)
    max_select: Optional[int] = Field(None, ge=1)
    required: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    #: When present, replaces the whole modifier list.
    modifiers: Optional[List[ModifierDTO]] = None


class ProductModifierGroupsDTO(BaseModel):
    """Which groups a product asks about, in order."""

    model_config = ConfigDict(populate_by_name=True)

    group_ids: List[str] = Field(default_factory=list)


class KitchenStationDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=100)
    branch_code: Optional[int] = None
    #: A print destination NAME, not a driver — a browser cannot address a
    #: thermal printer directly.
    printer_target: Optional[str] = Field(None, max_length=100)
    sort_order: int = Field(default=0, ge=0)


class ProductStationsDTO(BaseModel):
    """Stations a product's comanda prints to. Empty means it does not print."""

    model_config = ConfigDict(populate_by_name=True)

    station_ids: List[str] = Field(default_factory=list)
