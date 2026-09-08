from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComboItemResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    combo_item_id: str
    product_id: str
    description: Optional[str] = None
    #: Catalog price of ONE of this component, so the POS can compute the
    #: combo's discount without a second round trip.
    unit_price: Optional[float] = None
    quantity: float = 1
    sort_order: int = 0


class ComboResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    combo_product_id: str
    #: The combo's own price — NOT the sum of its parts.
    price: Optional[float] = None
    items: List[ComboItemResponse] = Field(default_factory=list)


class ModifierResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    modifier_id: str
    name: str
    price_delta: float = 0
    product_id: Optional[str] = None
    sort_order: int = 0


class ModifierGroupResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_id: str
    organization_id: str
    name: str
    min_select: int = 0
    max_select: Optional[int] = None
    required: bool = False
    sort_order: int = 0
    modifiers: List[ModifierResponse] = Field(default_factory=list)


class ModifierGroupListResponse(BaseModel):
    data: List[ModifierGroupResponse]


class KitchenStationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    station_id: str
    organization_id: str
    branch_id: Optional[str] = None
    name: str
    printer_target: Optional[str] = None
    sort_order: int = 0


class KitchenStationListResponse(BaseModel):
    data: List[KitchenStationResponse]
