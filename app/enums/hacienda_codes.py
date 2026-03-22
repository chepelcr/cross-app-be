"""Hacienda catalog code enums for Costa Rica e-invoicing."""

from enum import Enum


class ProductCodeType(str, Enum):
    VENDOR = "01"         # Código del producto del vendedor
    BUYER = "02"          # Código del producto del comprador
    MANUFACTURER = "03"   # Código del producto asignado por el fabricante
    INTERNAL = "04"       # Código uso interno
    OTHER = "99"          # Otros


class DiscountType(str, Enum):
    TRADE = "01"          # Descuento comercial
    VOLUME = "02"         # Descuento por volumen
    PROMOTIONAL = "03"    # Descuento promocional
    OTHER = "99"          # Otros (requires reason)


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
