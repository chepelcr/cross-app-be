"""Hacienda catalog code enums for Costa Rica e-invoicing (v4.4).

Scope: codes referenced by the product surface only. Sale-side enums
(DocumentType, SaleConditionCode, PaymentMethodCode, ReferenceDocType,
ReferenceCode, IdentificationTypeCode, OtherChargeCode) belong to the
sales service and are not duplicated here.
"""

from enum import Enum


class ProductCodeType(str, Enum):
    VENDOR = "01"         # Código del producto del vendedor
    BUYER = "02"          # Código del producto del comprador
    MANUFACTURER = "03"   # Código del producto asignado por el fabricante
    INTERNAL = "04"       # Código uso interno
    OTHER = "99"          # Otros


class DiscountType(str, Enum):
    """Discount nature codes per Hacienda Nota 20.

    Labels mirror the spec names so business logic reads naturally; the
    string values stay stable to preserve persisted JSONB payloads.

    Mirrors the `discount_types` catalog served by data-be (country 188).
    Only 01/03 re-route IVA to the factory — see
    FACTORY_ASSUMED_DISCOUNT_NATURES below — and only 99 requires a free-text
    reason, which is why COMMERCIAL (07) is the right default for an imported
    line that carries a discount but no type.
    """

    ROYALTY = "01"                     # Descuento por Regalía
    ROYALTY_BONUS_VAT_CUSTOMER = "02"  # Regalía / bonificación, IVA cobrado al cliente
    BONUS = "03"                       # Descuento por Bonificación
    VOLUME = "04"                      # Descuento por volumen
    SEASONAL = "05"                    # Descuento por Temporada (estacional)
    PROMOTIONAL = "06"                 # Descuento promocional
    COMMERCIAL = "07"                  # Descuento Comercial
    FREQUENCY = "08"                   # Descuento por frecuencia
    SUSTAINED = "09"                   # Descuento sostenido
    OTHER = "99"                       # Otros (requires reason)


class TaxType(str, Enum):
    IVA = "01"    # Impuesto al Valor Agregado
    ISC = "02"    # Impuesto Selectivo de Consumo
    IUC = "03"    # Impuesto Único a los Combustibles
    ISEBA = "04"  # Impuesto Específico de Bebidas Alcohólicas
    ISEBEC = "05" # Impuesto Específico sobre Bebidas Envasadas
    IPT = "06"    # Impuesto a los Productos de Tabaco
    IVACE = "07"  # IVA Cálculo Especial
    IVARBU = "08" # IVA Régimen de Bienes Usados
    ISEC = "12"   # Impuesto Específico al Cemento
    OTHERS = "99" # Otros


class TaxRateCode(str, Enum):
    """IVA rate codes per Hacienda Nota 8.1."""

    EXEMPT_FULL_CREDIT = "01"          # 0% — derecho a crédito pleno (Art. 32 RLIVA)
    REDUCED_1 = "02"                   # 1%
    REDUCED_2 = "03"                   # 2%
    REDUCED_4 = "04"                   # 4%
    TRANSITIONAL_0 = "05"              # 0% transitorio (NC/ND only)
    TRANSITIONAL_4 = "06"              # 4% transitorio (NC/ND only)
    TRANSITIONAL_8 = "07"              # 8% transitorio (NC/ND only, disabled)
    GENERAL_13 = "08"                  # 13% — tarifa general
    REDUCED_HALF = "09"                # 0.5%
    EXEMPT = "10"                      # 0% — exento (Ley 9635 Art. 8)
    NOT_SUBJECT = "11"                 # 0% — no sujeto, sin derecho de crédito


class IvaCollectedFactory(str, Enum):
    """`IVACobradoFabrica` indicator per Hacienda v4.4."""

    PRE_DETERMINED = "01"  # IVA pre-determinado a nivel de fábrica
    EXEMPT_BY_FACTORY = "02"  # Exento por régimen especial de fábrica


class CabysSpecialPrefix(str, Enum):
    """CABYS code prefixes that trigger special-tax branching.

    Used by `tax_calculation_service.apply_isebec` to pick between the
    non-alcoholic (water/soft-drinks) and alcoholic formulas.
    """

    ISEBEC_NON_ALCOHOLIC = "2202"  # Bebidas envasadas no alcohólicas
    ISEBEC_ALCOHOLIC = "3401"      # Bebidas alcohólicas


# Discount natures that re-route the line's IVA into
# `ImpuestoAsumidoEmisorFabrica` (Hacienda Nota 20). Mirrors the FE
# `FACTORY_ASSUMED_DISCOUNT_NATURES` constant.
FACTORY_ASSUMED_DISCOUNT_NATURES: tuple[str, ...] = (
    DiscountType.ROYALTY.value,
    DiscountType.BONUS.value,
)
