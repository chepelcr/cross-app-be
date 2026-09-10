from __future__ import annotations

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ManualOrderPartyDTO(BaseModel):
    """Denormalized client identity captured at the till."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=250)
    gln: Optional[str] = Field(None, max_length=50)
    internal_code: Optional[str] = Field(None, max_length=50)


class ManualOrderDeliveryLocationDTO(BaseModel):
    """Where the order goes — one of three shapes, never a free-text blob.

    * ``store``    — a point the client has registered (``store_id``)
    * ``receiver`` — the receiver's own address, copied as the CR cascade
    * ``custom``   — a hand-picked provincia/cantón/distrito/barrio + address
    """

    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["store", "receiver", "custom"] = "store"
    store_id: Optional[str] = None
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=250)
    gln: Optional[str] = Field(None, max_length=50)
    state_id: Optional[int] = None
    county_id: Optional[int] = None
    district_id: Optional[int] = None
    neighborhood_id: Optional[int] = None
    address: Optional[str] = Field(None, max_length=500)


class ManualOrderTaxSpecialFieldsDTO(BaseModel):
    """Per-unit parameters for the specific excises (codes 03/04/05/06/12).

    These taxes are not a rate on a base — each multiplies a per-unit amount by
    a quantity, a volume or a proportion — so a line that omits them cannot be
    recomputed at all, and an invoice built from the pedido later would have to
    invent them. Mirrors `TaxSpecialFieldsDTO` on the product side, which is the
    shape these are stored and recomputed in.
    """

    model_config = ConfigDict(populate_by_name=True)

    quantity: Optional[float] = Field(None, ge=0)
    percentage: Optional[float] = Field(None, ge=0)
    proportion: Optional[float] = Field(None, ge=0)
    volume_consumption: Optional[float] = Field(None, ge=0)
    #: data-api catalog id of the per-unit amount (`tax_amounts`).
    #: Accepts an int as well as a string: the FE types it as a number (the
    #: catalog serves integer ids) while everything downstream keys on the
    #: string, and a strict `str` here rejects the POS's own payload.
    tax_amount_id: Optional[Union[str, int]] = Field(None)
    #: The per-unit amount itself, so the pedido can be recomputed offline.
    tax_unit_amount: Optional[float] = Field(None, ge=0)


class ManualOrderTaxDTO(BaseModel):
    """Per-line tax breakdown. Kept structured so the server can recompute."""

    model_config = ConfigDict(populate_by_name=True)

    code: Optional[str] = Field(None, max_length=4, description="Hacienda tax type code")
    rate_code: Optional[str] = Field(None, max_length=4)
    rate: Optional[float] = Field(None, ge=0)
    base: Optional[float] = Field(None, ge=0)
    amount: Optional[float] = Field(None, ge=0)
    factory_assumed: Optional[bool] = False
    #: Required when code = "99" (Otros).
    other_tax_type: Optional[str] = Field(None, max_length=100)
    #: `FactorCalculoIVA` for code "08" (régimen de bienes usados).
    factor: Optional[float] = Field(None, ge=0)
    special_fields: Optional[ManualOrderTaxSpecialFieldsDTO] = None


class ManualOrderDiscountDTO(BaseModel):
    """Per-line discount in the Hacienda cascade order."""

    model_config = ConfigDict(populate_by_name=True)

    code: Optional[str] = Field(None, max_length=4)
    nature: Optional[str] = Field(None, max_length=100)
    percentage: Optional[float] = Field(None, ge=0, le=100)
    amount: Optional[float] = Field(None, ge=0)


class ManualOrderLineDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    line_number: int = Field(..., ge=1)
    product_id: Optional[str] = Field(None, max_length=255)
    internal_code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1, max_length=500)
    quantity: float = Field(..., gt=0)
    #: Unit price WITHOUT tax.
    unit_price: float = Field(..., ge=0)
    discount: float = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    line_total: float = Field(default=0, ge=0)
    #: Kept even though a pedido is not fiscal — it is what makes billing it
    #: later possible without guessing a rate.
    cabys: Optional[str] = Field(None, max_length=13)
    taxes: Optional[List[ManualOrderTaxDTO]] = None
    discounts: Optional[List[ManualOrderDiscountDTO]] = None


class ManualOrderPaymentDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(..., max_length=4, description="Hacienda payment code")
    other_type: Optional[str] = Field(None, max_length=100)
    amount: float = Field(..., ge=0)


class ManualOrderTotalsDTO(BaseModel):
    """Client-side totals. A HINT only — the server recomputes (see service)."""

    model_config = ConfigDict(populate_by_name=True)

    total_lines: int = Field(default=0, ge=0)
    total_quantity_ordered: float = Field(default=0, ge=0)
    subtotal: float = Field(default=0, ge=0)
    discounts: float = Field(default=0, ge=0)
    taxes: float = Field(default=0, ge=0)
    grand_total: float = Field(default=0, ge=0)


class CreateManualOrderDTO(BaseModel):
    """A pedido captured by hand in the POS document editor.

    Discriminated from the anonymous storefront pedido by ``source='manual'``
    on the shared ``POST /orders`` route: the storefront body has no ``source``.
    """

    model_config = ConfigDict(populate_by_name=True)

    source: Literal["manual"]
    #: Internal editor doc type ('PM'), never a Hacienda code.
    document_type: str = Field(default="PM", max_length=8)
    #: 'work_order' for a taller OT; None for a plain pedido. NEVER '73' —
    #: that is the cross-docking flow.
    order_type: Optional[str] = Field(None, max_length=20)

    #: User-writable. Omit to draw from the organization's PM sequence.
    document_number: Optional[str] = Field(None, max_length=50)
    #: Save as a cotización — the order opens in 'quote' status.
    is_quote: bool = False

    client_id: Optional[str] = None
    client: ManualOrderPartyDTO

    #: Captured so a later factura reuses what the cashier chose.
    sale_condition: Optional[str] = Field(None, max_length=10)
    activity_code: Optional[str] = Field(None, max_length=20)
    credit_term: Optional[str] = Field(None, max_length=10)

    delivery_date: Optional[str] = Field(None, max_length=20)
    delivery_location: Optional[ManualOrderDeliveryLocationDTO] = None
    department_id: Optional[str] = None

    #: Taller (work_order) fields — the per-visit facts, not the asset itself.
    asset_id: Optional[str] = None
    odometer: Optional[int] = Field(None, ge=0)
    reported_issue: Optional[str] = Field(None, max_length=500)

    event: Optional[str] = Field(None, max_length=50)
    comment: Optional[str] = Field(None, max_length=500)

    currency_code: str = Field(default="CRC", max_length=3)
    exchange_rate: float = Field(default=1, gt=0)

    assignment_id: Optional[str] = Field(None, max_length=255)
    branch_number: Optional[int] = None
    terminal_number: Optional[int] = None

    #: May be empty: a pedido is normally settled after delivery.
    payments: List[ManualOrderPaymentDTO] = Field(default_factory=list)
    lines: List[ManualOrderLineDTO] = Field(..., min_length=1)
    totals: Optional[ManualOrderTotalsDTO] = None
