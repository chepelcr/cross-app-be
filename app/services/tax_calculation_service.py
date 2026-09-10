"""Tax calculation service — one method per Hacienda tax code (v4.4 Nota 7).

Pure Decimal math, no DB, no Pydantic mutation. Each `apply_*` method returns
a `TaxLineRow` plus a few side-channel deltas (additions to `base_amount`, the
factory-assumed flag). The orchestrator `compute_line_taxes` assembles them.

Operates on `ProductTaxDTO` shaped inputs but only reads attribute paths —
no mutation, no `dict.get`.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dtos.common.calculation_results import LineTaxResult, TaxLineRow
from app.dtos.requests.product_request_dto import ProductTaxDTO
from app.enums.hacienda_codes import (
    CabysSpecialPrefix,
    FACTORY_ASSUMED_EXCISES,
    IvaCollectedFactory,
    TaxType,
)

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")

# `CantidadUnidadMedida` and `VolumenUnidadConsumo` carry a TIGHTER XSD limit
# than every other numeric field on the line — 2 fraction digits, not 5:
#
#   cvc-fractionDigits-valid: Value '0.35500' has 3 fraction digits, but the
#   number of fraction digits has been limited to 2.
#
# This is the millilitre trap. Bottle sizes that divide cleanly into litres
# (700 ml, 750 ml, 1 L) are expressible; the common can and bottle sizes are
# not — 355 ml is 0.355 L and is rejected on the SCHEMA, before any arithmetic
# is checked. Quantizing here rather than at the XML seam is deliberate: the
# amount has to be derived from the volume the document will actually declare,
# or the declared quantity and the declared amount disagree.
_CANTIDAD_UM_QUANT = Decimal("0.01")
#: `Proporcion` allows 5 (TotalDigits=10, FractionDigits=5).
_PROPORCION_QUANT = Decimal("0.00001")
_AMOUNT_QUANT = Decimal("0.00001")


def _d(value, default: str = "0") -> Decimal:
    """Decimal coercion that tolerates None / int / float / str / Decimal."""
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q(value: Decimal, quant: Decimal) -> Decimal:
    """Quantize, collapsing zero so it never serializes as ``0E-8``."""
    result = value.quantize(quant, rounding=ROUND_HALF_UP)
    return ZERO if result == 0 else result


def _q_cantidad_um(value) -> Decimal:
    """Quantize a volume/quantity field to the 2 fraction digits the XSD allows."""
    return _q(_d(value), _CANTIDAD_UM_QUANT)


def _q_proporcion(value) -> Decimal:
    return _q(_d(value), _PROPORCION_QUANT)


def _q_amount(value) -> Decimal:
    """Quantize a money amount to the 5 decimals the Hacienda XSD allows.

    Applied per TAX ROW rather than once at the end, because that is where the
    biller rounds: each `MontoImpuesto` in the XML is a 5-decimal figure and
    Hacienda re-adds them. Summing unrounded intermediates and rounding the
    total produces a number that can differ from the document's own arithmetic
    by a céntimo, which is enough for -45.
    """
    return _q(_d(value), _AMOUNT_QUANT)


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
        """Compute IVA.

        When `use_original_base` is True — a royalty (01) or bonus (03) discount
        is on the line — the tax is computed on `monto_total_original`, the
        PRE-discount line subtotal, because Nota 20 leaves those natures' base
        un-eroded. Every other nature, 02 included, taxes the discounted base.
        """
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        effective_base = (
            _d(monto_total_original)
            if use_original_base and monto_total_original is not None
            else base_amount
        )
        amount = _q_amount(effective_base * rate / HUNDRED)
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
        amount = _q_amount(subtotal * rate / HUNDRED)
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
        amount = _q_amount(qty * unit_amount)
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
        """ISEBA (04) — bebidas alcohólicas.

            Proporcion = CantidadUnidadMedida x (Porcentaje / 100)
            Monto      = Cantidad x Proporcion x ImpuestoUnidad

        Both intermediate figures are quantized to the limits the document will
        declare them at BEFORE the amount is derived from them. That ordering is
        the whole point: Hacienda recomputes the amount from the `Proporcion`
        and `CantidadUnidadMedida` in the XML, so an amount derived from the raw
        0.355 L disagrees with the 0.36 the document actually carries.
        """
        sf = tax.special_fields
        unit_amount = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        # The volume is capped at 2 fraction digits — see _CANTIDAD_UM_QUANT.
        qty = _q_cantidad_um(sf.quantity if sf else None) or ONE
        pct = _d(sf.percentage if sf else None)
        proportion = _q_proporcion(qty * pct / HUNDRED)
        amount = _q_amount(detail_quantity * proportion * unit_amount)
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
        """ISEBEC (05) — one tax code, two formulas.

        Verbatim from the Hacienda calculation rules:

            Bebidas: "la multiplicación del campo Cantidad por el campo
              Cantidad de la unidad de medida a utilizar, multiplicado por el
              resultado de DIVIDIR el campo Impuesto por Unidad entre el campo
              Volumen por Unidad de Consumo."
                Monto = Cantidad x CantidadUnidadMedida
                        x (ImpuestoUnidad / VolumenUnidadConsumo)

            Jabón de tocador: "la multiplicación del campo Cantidad por el
              campo Volumen por Unidad de Consumo por Impuesto por Unidad."
                Monto = Cantidad x VolumenUnidadConsumo x ImpuestoUnidad

        Note what flips, because it is easy to get backwards: soap MULTIPLIES by
        `VolumenUnidadConsumo` where beverages DIVIDE by it, and soap does not
        use `CantidadUnidadMedida` at all. The field carries a different unit in
        each case — grams for soap, litres of consumption volume for a drink.

        The branch used to test CABYS prefix "2202", a Harmonized System heading
        that matches no CABYS at all, so the divisor was never applied and every
        line — beverages included — took the soap formula.

        Not implemented: the "Detalle de productos del surtido, paquetes o
        combos" variant, where this amount is the sum of the individual código-05
        amounts of the surtido detail lines, multiplied by the main line's
        quantity when it carries more than one surtido unit. The surtido node is
        not modelled anywhere in the stack yet, so there is nothing to sum.
        """
        sf = tax.special_fields
        tax_unit = _d(sf.tax_amount.amount if sf and sf.tax_amount else None)
        qty = _q_cantidad_um(sf.quantity if sf else None) or ONE
        vol = _q_cantidad_um(sf.volume_consumption if sf else None)

        if cabys_code and cabys_code.startswith(
            CabysSpecialPrefix.ISEBEC_TOILET_SOAP.value
        ):
            amount = _q_amount(detail_quantity * vol * tax_unit)
        elif not vol:
            # Dividing by a missing consumption volume is not a defensible
            # guess; zero is at least visibly wrong on the totals.
            amount = ZERO
        else:
            amount = _q_amount(detail_quantity * qty * (tax_unit / vol))

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
        amount = _q_amount(detail_quantity * qty * unit_amount)
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
        amount = _q_amount(effective_base * rate / HUNDRED)
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
        amount = _q_amount(factor * effective_base)
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
        amount = _q_amount(subtotal * rate / HUNDRED)
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.ISEC.value,
                amount=amount,
                base_amount=subtotal,
            ),
            add_to_base=amount,
        )

    def apply_others(self, tax: ProductTaxDTO, subtotal: Decimal) -> _TaxStepOutput:
        """OTHERS (99) — a plain rate on the line SUBTOTAL.

        It used to price off the excise-inflated base, which put it on a
        different number from the one the biller uses: `TaxService` builds every
        rate-driven row (02, 12, 99) against `line_subtotal` and reserves the
        excise-inclusive base for the IVA family alone. -45 checks the amount
        against `base imponible x tarifa`, so the two have to agree.
        """
        rate = _d(tax.tax_rate.percentage if tax.tax_rate else None)
        amount = _q_amount(subtotal * rate / HUNDRED)
        return _TaxStepOutput(
            row=TaxLineRow(
                tax_type_id=TaxType.OTHERS.value,
                amount=amount,
                base_amount=subtotal,
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
        monto_total_original: Optional[Decimal] = None,
        ivace_base_override: Optional[Decimal] = None,
        iva_collected_factory: Optional[str] = None,
    ) -> LineTaxResult:
        """Compute every tax row for a line, in the Hacienda-mandated order.

        Order (mirrors the biller's `TaxService` and Hacienda Nota 7):

        1. Special / per-unit codes (02, 03, 04, 05, 06, 12). Four of them —
           02 ISC, 04 ISEBA, 05 ISEBEC, 12 ISEC — grow the IVA base (-454);
           03 IUC and 06 IPT do not.
        2. OTHERS (99) — a rate on the line subtotal, like every other
           rate-driven code.
        3. IVA family (01, 07, 08) — priced on the excise-inclusive base.

        **Who pays each row is decided per TAX ROW, not per line.** Two separate
        rules put an amount into `factory_assumed_tax` instead of `net_tax`:

        * `FACTORY_ASSUMED_EXCISES` (03, 04, 05, 12) are absorbed by the issuer
          *always*, whatever the discounts are (-476). The IVA on the same line
          may still be charged to the customer — which is exactly why this is
          not a line-level flag.
        * The LINE assumes its IVA when a royalty/bonus discount (natures 01/03,
          Nota 20) is present, or when `iva_collected_factory == "01"` — VAT
          settled at the factory. Hacienda answers -451 when the latter is
          missed.

        Nature **02** ("Regalía/bonificación con IVA cobrado al cliente") used to
        get its own un-eroded base here. It no longer does: Hacienda rejects a
        document built that way with -45 and -454 together, which pin
        `ImpuestoNeto` to `BaseImponible x tarifa` and `BaseImponible` to the
        DISCOUNTED subtotal, leaving a customer-paid tax on the original amount
        unrepresentable. Verified empirically at 3% and at 100%; 01 and 03 escape
        the same check only because they assume the tax outright.
        """
        base_amount = (
            ivace_base_override if ivace_base_override is not None else subtotal
        )
        per_tax: List[TaxLineRow] = []
        iva_total = ZERO
        other_total = ZERO
        factory_assumed = ZERO
        net_tax = ZERO

        # The LINE absorbs its own IVA under either of two independent rules —
        # see the docstring. Both have to be consulted in one place, because the
        # per-line figure and the summary that rolls it up must agree or the
        # totals differ by exactly the tax.
        line_assumes = bool(royalty_bonus_present) or (
            (iva_collected_factory or "").strip()
            == IvaCollectedFactory.PRE_DETERMINED.value
        )

        def _record(row: TaxLineRow, *, assumed: bool, is_iva: bool) -> None:
            """File one computed row under net or factory-assumed."""
            nonlocal iva_total, other_total, factory_assumed, net_tax
            if assumed:
                factory_assumed += row.amount
                per_tax.append(
                    row.model_copy(update={"factory_assumed_amount": row.amount})
                )
                return
            if is_iva:
                iva_total += row.amount
            else:
                other_total += row.amount
            net_tax += row.amount
            per_tax.append(row)

        # Pass 1 — special / per-unit codes. Four of them grow the IVA base;
        # four of them (a different four) are absorbed by the issuer outright.
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
            # An assumed excise STILL builds the IVA base: -454's formula reads
            # the amounts off the line, not off who pays them.
            base_amount += step.add_to_base
            _record(
                step.row,
                assumed=code in FACTORY_ASSUMED_EXCISES,
                is_iva=False,
            )

        # Pass 2 — OTHERS (99), a rate on the subtotal like every other
        # rate-driven code. Never re-routed: 99 is a collected tax.
        for t in taxes:
            if t.tax_type_id == TaxType.OTHERS.value:
                step = self.apply_others(t, subtotal)
                _record(step.row, assumed=False, is_iva=False)

        # Pass 3 — IVA family, priced on the excise-inclusive base. Royalty and
        # bonus natures additionally price it on the PRE-discount amount, since
        # Nota 20 leaves their base un-eroded.
        for t in taxes:
            code = t.tax_type_id
            if code == TaxType.IVA.value:
                step = self.apply_iva(
                    t,
                    base_amount,
                    monto_total_original=monto_total_original,
                    use_original_base=royalty_bonus_present,
                )
            elif code == TaxType.IVACE.value:
                step = self.apply_ivace(
                    t,
                    base_amount,
                    monto_total_original=monto_total_original,
                    use_original_base=royalty_bonus_present,
                )
            elif code == TaxType.IVARBU.value:
                step = self.apply_ivarbu(
                    t,
                    subtotal,
                    monto_total_original=monto_total_original,
                    use_original_base=royalty_bonus_present,
                )
            else:
                continue

            _record(step.row, assumed=line_assumes, is_iva=True)

        # `net_tax` is what the buyer owes; factory-assumed is owed upstream by
        # the factory and is reported separately (TotalImpAsumEmisorFabrica).
        return LineTaxResult(
            iva_tax_total=iva_total,
            other_tax_total=other_total,
            factory_assumed_tax=factory_assumed,
            net_tax=net_tax,
            base_amount=base_amount,
            per_tax=per_tax,
        )
