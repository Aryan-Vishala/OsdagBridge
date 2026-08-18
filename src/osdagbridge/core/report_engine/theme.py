# =============================================================================
# ReportTheme — Single immutable formatting source for the entire report.
#
# Created once at report generation time.  Only the renderer sees it.
# Chapters never import or reference the theme directly.
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class PageGeometry:
    width_mm: float = 210
    height_mm: float = 297
    margin_top_mm: float = 20
    margin_bottom_mm: float = 25
    margin_left_mm: float = 20
    margin_right_mm: float = 20
    footer_reserve_mm: float = 15


@dataclass(frozen=True)
class TableStyle:
    column_padding_pt: float = 6
    row_height_pt: float = 14
    font_size_pt: float = 11
    header_bg_color: str = "lightgray"
    border_width_pt: float = 0.5


@dataclass(frozen=True)
class ChartStyle:
    width_cm: float = 12
    height_cm: float = 8
    dpi: int = 300
    title_font_size: int = 12


@dataclass(frozen=True)
class TypographyStyle:
    main_font: str = "Computer Modern"
    main_font_size_pt: float = 11
    heading_font_size_pt: float = 14


@dataclass(frozen=True)
class ColorPalette:
    primary: str = "#003366"
    accent: str = "#FF6600"
    error: str = "#DD0000"
    success: str = "#00AA00"


@dataclass(frozen=True)
class ReportTheme:
    """Immutable formatting source.  Constructed once; never modified."""

    page: PageGeometry = field(default_factory=PageGeometry)
    table_styles: Dict[str, TableStyle] = field(default_factory=lambda: {
        "default": TableStyle(),
        "compact": TableStyle(column_padding_pt=4, row_height_pt=12),
        "load": TableStyle(column_padding_pt=5, row_height_pt=13),
    })
    chart: ChartStyle = field(default_factory=ChartStyle)
    typography: TypographyStyle = field(default_factory=TypographyStyle)
    colors: ColorPalette = field(default_factory=ColorPalette)
