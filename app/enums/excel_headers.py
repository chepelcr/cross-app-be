from enum import Enum


class ExcelHeader(Enum):
    """
    Enumeration of Excel header aliases for DETALLES file parsing.

    Each member is a tuple of (field_name, [header_aliases]) where:
    - field_name: Internal field identifier used in the parser
    - aliases: List of possible Excel column header names across file versions
    """

    # Order metadata
    DOCUMENT_NUMBER = ("document_number", ["Numero Doc", "NUM_DOC"])
    CLIENT_NAME = ("client_name", ["Nombre Cliente", "NOMBRE_CLIENTE"])
    CREATION_DATE = ("creation_date", ["Fecha Creación", "FECHA_DOC"])
    DELIVERY_DATE = ("delivery_date", ["Fecha Entrega", "FECHA_ENTREGA"])
    DELIVER_TO = ("deliver_to", ["Entregar en", "NOMBRE_DESPACHO"])
    DISCOUNTS = ("discounts", ["Descuentos", "DESCUENTOS"])
    TAXES = ("taxes", ["Impuestos", "IMPUESTOS"])
    GRAND_TOTAL = ("grand_total", ["Total General", "TOTAL"])
    TOTAL_QUANTITIES = ("total_quantities", ["Total Cantidades", "TOTAL_CANTIDAD"])
    SUPPLIER_NAME = ("supplier_name", ["Nombre Proveedor", "NOMBRE_PROVEE"])
    CLIENT_GLN = ("client_gln", ["GLN_CLIENTE"])
    LINE_COUNT = ("line_count", ["Cant. Lineas", "CANT_LINEAS"])
    DISPATCH_GLN = ("dispatch_gln", ["Gln Despacho", "GLN_DESPACHO"])
    DOCUMENT_TYPE = ("document_type", ["Tipo Doc", "TIPO_DOC"])
    SUPPLIER_GLN = ("supplier_gln", ["Gln Proveedor", "GLN_PROVEEDOR"])
    SUPPLIER_INTERNAL_CODE = (
        "supplier_internal_code",
        ["Cod Interno Proveedor", "Cod Int Proveedor", "COD_INTER_PROVEE", "NUM_VENDEDOR"],
    )
    BGM011 = ("bgm011", ["BGM011"])
    ORDER_TYPE = ("order_type", ["Tipo Orden", "RFFZZZ"])
    EVENT = ("event", ["Evento", "EVENTO"])
    DEPARTMENT = ("department", ["Dpto", "DEPARTAMENTO"])
    LATITUDE = ("latitude", ["Latitud", "LATITUD"])
    LONGITUDE = ("longitude", ["Longitud", "LONGITUD"])
    COMMENT = ("comment", ["Comentario", "COMENTARIO"])

    # Line item fields
    LINE_NUMBER = ("line_number", ["Línea"])
    INTERNAL_CODE = ("internal_code", ["Cod. Interno"])
    CODE = ("code", ["Código"])
    CLIENT_ARTICLE_CODE = ("client_article_code", ["Cod.Artic.Cliente"])
    DESCRIPTION = ("description", ["Descripción"])
    QUANTITY_ORDERED = ("quantity_ordered", ["Cantidad Pedida"])
    UNITS_ORDERED = ("units_ordered", ["Unidades Pedidas"])
    UNIT_PRICE = ("unit_price", ["Precio Unidad"])
    DISCOUNT = ("discount", ["Descuento"])
    LINE_TOTAL = ("line_total", ["Total Línea"])
    TAX = ("tax", ["Impuesto"])
    QUANTITY_DISPATCHED = ("quantity_dispatched", ["Cantidad Despachada"])
    DISPATCH_REJECTION_REASON = (
        "dispatch_rejection_reason",
        ["Motivo de no Despacho"],
    )
    QUANTITY_RECEIVED = ("quantity_received", ["Cantidad Recibida"])
    ARTICLE_CODE = ("article_code", ["COD_ARTIC"])

    def __init__(self, field_name: str, aliases: list[str]) -> None:
        self._field_name = field_name
        self._aliases = aliases

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def aliases(self) -> list[str]:
        return self._aliases

    @classmethod
    def build_header_map(cls, headers: list[str]) -> dict["ExcelHeader", int]:
        """
        Build a mapping from ExcelHeader members to column indices
        based on the actual headers found in the file.
        """
        header_map: dict[ExcelHeader, int] = {}
        for member in cls:
            for alias in member.aliases:
                if alias in headers:
                    header_map[member] = headers.index(alias)
                    break
        return header_map
