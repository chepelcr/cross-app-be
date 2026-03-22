"""Color scheme enums and palettes for crossdocking reports."""

from enum import Enum
from typing import Dict


class ReportColorScheme(str, Enum):
    GREEN = "green"
    ORANGE = "orange"
    BLUE = "blue"
    GREEN_ALT = "green_alt"


_PALETTES: Dict[str, dict] = {
    "green": {
        "hdr_dark": "#0e5c23",
        "hdr_med": "#2e6b34",
        "hdr_light": "#0e5c23",
        "hdr_light_text": "#fff",
        "row_light": "#d4edda",
        "row_alt": "#e8f5e9",
        "excel_header": "0E5C23",
    },
    "orange": {
        "hdr_dark": "#c65811",
        "hdr_med": "#c65811",
        "hdr_light": "#e7b189",
        "hdr_light_text": "#000",
        "row_light": "#f7caad",
        "row_alt": "#fce3d6",
        "excel_header": "C65811",
    },
    "blue": {
        "hdr_dark": "#1e4e77",
        "hdr_med": "#0070c0",
        "hdr_light": "#0070c0",
        "hdr_light_text": "#fff",
        "row_light": "#9ac1e6",
        "row_alt": "#b4c6e7",
        "excel_header": "1E4E77",
    },
    "green_alt": {
        "hdr_dark": "#375522",
        "hdr_med": "#548134",
        "hdr_light": "#8ab96b",
        "hdr_light_text": "#000",
        "row_light": "#a9d08d",
        "row_alt": "#c6e0b4",
        "excel_header": "375522",
    },
}


def get_color_palette(scheme) -> dict:
    """Return the color palette dict for the given scheme. Defaults to green."""
    if isinstance(scheme, ReportColorScheme):
        key = scheme.value
    else:
        key = str(scheme) if scheme else "green"
    return _PALETTES.get(key, _PALETTES["green"])
