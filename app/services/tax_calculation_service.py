"""Tax calculation service — one method per Hacienda tax code (v4.4 Nota 7).

Pure Decimal math, no DB, no Pydantic mutation. Each `apply_*` method returns
a `TaxLineRow` plus a few side-channel deltas (additions to `base_amount`, the
factory-assumed flag). The orchestrator `compute_line_taxes` assembles them.

Operates on `ProductTaxDTO` shaped inputs but only reads attribute paths —
no mutation, no `dict.get`.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.common.calculation_results import LineTaxResult, TaxLineRow
from app.dtos.requests.product_request_dto import ProductTaxDTO
from app.enums.hacienda_codes import CabysSpecialPrefix, TaxType

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def _d(value, default: str = "0") -> Decimal:
    """Decimal coercion that tolerates None / int / float / str / Decimal."""
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class _TaxStepOutput(BaseModel):
    """Internal — what one `apply_*` returns to the orchestrator."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    row: TaxLineRow
    add_to_base: Decimal = Field(default=ZERO)
    counts_as_iva: bool = Field(default=False)
    # `apply_isebec` / IVACE base override pass an integer here so the
    # orchestrator can update its running base before downstream codes run.
    base_override: Optional[Decimal] = Field(default=None)


class TaxCalculator:
    """Per-Hacienda-code tax math.

    Construction is stateless; every method is conceptually pure but takes the
    necessary slice of orchestrator state.
    """

    # ---- Standard percentage codes -----------------------------------------
    def apply_iva(
        self,
        tax: ProductTaxDTO,
        base_amount: Decimal,
        *,
        monto_total_original: Optional[Decimal] = None,
        use_original_base: bool = False,
    ) -> _TaxStepOutput:
        """Compute IVA. When `use_original_base` is True (royalty/bonus codes
        01/03 or code-02 customer-pays-on-original), tax is computed on
        `monto_total_original` (pre-discount line subtotal) per Hacienda Nota 20.
        """
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        effective_base = (
            _d(monto_total_original)
            if use_original_base and monto_total_original is not None
            else base_amount
        )
        amount = effective_base * rate / HUNDRED
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.IVA.value,
                amount=amount,
                base_amount=effective_base,
            ),
            counts_as_iva=True,
        )

    def apply_isc(self, tax: ProductTaxDTO, subtotal: Decimal) -> _TaxStepOutput:
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        amount = subtotal * rate / HUNDRED
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.ISC.value,
                amount=amount,
                base_amount=subtotal,
            ),
            add_to_base=amount,
        )

    def apply_iuc(self, tax: ProductTaxDTO) -> _TaxStepOutput:
        sf = tax.special_fields
        unit_amount = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        qty = _d(sf.quantity if sf else None) or ONE
        amount = qty * unit_amount
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.IUC.value,
                amount=amount,
                base_amount=ZERO,
            ),
        )

    def apply_iseba(
        self, tax: ProductTaxDTO, detail_quantity: Decimal
    ) -> _TaxStepOutput:
        sf = tax.special_fields
        unit_amount = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        qty = _d(sf.quantity if sf else None) or ONE
        pct = _d(sf.percentage if sf else None)
        amount = detail_quantity * (qty * pct / HUNDRED) * unit_amount
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.ISEBA.value,
                amount=amount,
                base_amount=ZERO,
            ),
            add_to_base=amount,
        )

    def apply_isebec(
        self,
        tax: ProductTaxDTO,
        detail_quantity: Decimal,
        cabys_code: Optional[str],
    ) -> _TaxStepOutput:
        sf = tax.special_fields
        tax_unit = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        qty = _d(sf.quantity if sf else None) or ONE
        vol = _d(sf.volume_consumption if sf else None) or ONE
        if cabys_code and cabys_code.startswith(
            CabysSpecialPrefix.ISEBEC_NON_ALCOHOLIC.value
        ):
            amount = detail_quantity * qty * (tax_unit / vol)
        else:
            amount = qty * vol * tax_unit
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.ISEBEC.value,
                amount=amount,
                base_amount=ZERO,
            ),
            add_to_base=amount,
        )

    def apply_ipt(
        self, tax: ProductTaxDTO, detail_quantity: Decimal
    ) -> _TaxStepOutput:
        sf = tax.special_fields
        unit_amount = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        qty = _d(sf.quantity if sf else None) or ONE
        amount = detail_quantity * qty * unit_amount
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.IPT.value,
                amount=amount,
                base_amount=ZERO,
            ),
        )

    def apply_ivace(
        self,
        tax: ProductTaxDTO,
        base_amount: Decimal,
        *,
        monto_total_original: Optional[Decimal] = None,
        use_original_base: bool = False,
    ) -> _TaxStepOutput:
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        effective_base = (
            _d(monto_total_original)
            if use_original_base and monto_total_original is not None
            else base_amount
        )
        amount = effective_base * rate / HUNDRED
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.IVACE.value,
                amount=amount,
                base_amount=effective_base,
            ),
            counts_as_iva=True,
        )

    def apply_ivarbu(
        self,
        tax: ProductTaxDTO,
        subtotal: Decimal,
        *,
        monto_total_original: Optional[Decimal] = None,
        use_original_base: bool = False,
    ) -> _TaxStepOutput:
        factor = _d(tax.tax_factor.factor if tax.tax_factor else None)
        effective_base = (
            _d(monto_total_original)
            if use_original_base and monto_total_original is not None
            else subtotal
        )
        amount = factor * effective_base
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.IVARBU.value,
                amount=amount,
                base_amount=effective_base,
            ),
            counts_as_iva=True,
        )

    def apply_isec(self, tax: ProductTaxDTO, subtotal: Decimal) -> _TaxStepOutput:
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        amount = subtotal * rate / HUNDRED
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.ISEC.value,
                amount=amount,
                base_amount=subtotal,
            ),
            add_to_base=amount,
        )

    def apply_others(self, tax: ProductTaxDTO, base_amount: Decimal) -> _TaxStepOutput:
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        amount = base_amount * rate / HUNDRED
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.OTHERS.value,
                amount=amount,
                base_amount=base_amount,
            ),
        )

    # ---- Orchestrator ------------------------------------------------------

    def compute_line_taxes(
        self,
        taxes: List[ProductTaxDTO],
        subtotal: Decimal,
        detail_quantity: Decimal,
        cabys_code: Optional[str],
        royalty_bonus_present: bool = False,
        customer_pays_tax_on_original_base: bool = False,
        monto_total_original: Optional[Decimal] = None,
        ivace_base_override: Optional[Decimal] = None,
    ) -> LineTaxResult:
        """Compute every tax row for a line, in the Hacienda-mandated order.

        Order (mirrors the FE engine and Hacienda Nota 7):
        1) Special / per-unit codes (02, 03, 04, 05, 06, 12) — some grow `base_amount`.
        2) OTHERS (99) — applied to the now-updated `base_amount`.
        3) IVA family (01, 07, 08) — final pass on `base_amount`.

        Flags only affect the IVA family (Pass 3):
        - `royalty_bonus_present` (codes 01/03 discount) computes IVA on
          `monto_total_original` AND routes the result to `factory_assumed_tax`.
        - `customer_pays_tax_on_original_base` (code 02 discount) computes IVA
          on `monto_total_original` but keeps the result in `net_tax`.
        Special / OTHERS codes are never re-routed by these flags.
        """
        base_amount = (
            ivace_base_override if ivace_base_override is not None else subtotal
        )
        per_tax: List[TaxLineRow] = []
        iva_total = ZERO
        other_total = ZERO
        factory_assumed = ZERO
        net_tax = ZERO

        # Pass 1 — special / per-unit codes. These NEVER re-route based on the
        # royalty/bonus or code-02 flags; only IVA does.
        for t in taxes:
            code = t.tax_type_id
            if code == TaxType.ISC.value:
                step = self.apply_isc(t, subtotal)
            elif code == TaxType.IUC.value:
                step = self.apply_iuc(t)
            elif code == TaxType.ISEBA.value:
                step = self.apply_iseba(t, detail_quantity)
            elif code == TaxType.ISEBEC.value:
                step = self.apply_isebec(t, detail_quantity, cabys_code)
            elif code == TaxType.IPT.value:
                step = self.apply_ipt(t, detail_quantity)
            elif code == TaxType.ISEC.value:
                step = self.apply_isec(t, subtotal)
            else:
                continue
            base_amount += step.add_to_base
            other_total += step.row.amount
            net_tax += step.row.amount
            per_tax.append(step.row)

        # Pass 2 — OTHERS (99), applied to the now-updated base. Likewise
        # untouched by the IVA-only flags.
        for t in taxes:
            if t.tax_type_id == TaxType.OTHERS.value:
                step = self.apply_others(t, base_amount)
                other_total += step.row.amount
                net_tax += step.row.amount
                per_tax.append(step.row)

        # Pass 3 — IVA family. The flags here switch the base to the pre-discount
        # `monto_total_original` and (only for royalty/bonus) re-route to
        # factory-assumed.
        use_original_base = royalty_bonus_present or customer_pays_tax_on_original_base
        for t in taxes:
            code = t.tax_type_id
            if code == TaxType.IVA.value:
                step = self.apply_iva(
                    t,
                    base_amount,
                    monto_total_original=monto_total_original,
                    use_original_base=use_original_base,
                )
            elif code == TaxType.IVACE.value:
                step = self.apply_ivace(
                    t,
                    base_amount,
                    monto_total_original=monto_total_original,
                    use_original_base=use_original_base,
                )
            elif code == TaxType.IVARBU.value:
                step = self.apply_ivarbu(
                    t,
                    subtotal,
                    monto_total_original=monto_total_original,
                    use_original_base=use_original_base,
                )
            else:
                continue

            if royalty_bonus_present:
                # IVA routes into factory-assumed, not net. Code 02 alone does
                # NOT trigger this — the customer still pays.
                factory_assumed += step.row.amount
                row = step.row.model_copy(
                    update={"factory_assumed_amount": step.row.amount}
                )
                per_tax.append(row)
            else:
                iva_total += step.row.amount
                net_tax += step.row.amount
                per_tax.append(step.row)

        # We discount factory-assumed out of out-the-door obligations only;
        # the FE mirrors this convention.
        return LineTaxResult(
            iva_tax_total=iva_total,
            other_tax_total=other_total,
            factory_assumed_tax=factory_assumed,
            net_tax=net_tax,
            base_amount=base_amount,
            per_tax=per_tax,
        )
