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
    row_height_factor: float = 1.15
    font_size: str = "normalsize"
    header_bg_color: str = "lightgray"
    rule_width_pt: float = 0.5
    caption_spacing_pt: float = 6


@dataclass(frozen=True)
class ChartStyle:
    width_cm: float = 12
    height_cm: float = 8
    dpi: int = 300
    title_font_size: int = 12
    annotation_font_size: int = 10
    threshold_linewidth: int = 2
    threshold_linestyle: str = "--"


@dataclass(frozen=True)
class TypographyStyle:
    main_font: str = "Computer Modern"
    main_font_size_pt: float = 11
    heading_font_size_pt: float = 14
    caption_font_weight: str = "bold"


@dataclass(frozen=True)
class ColorPalette:
    primary: str = "#003366"
    secondary: str = "#444444"
    accent: str = "#FF6600"
    error: str = "#DD0000"
    success: str = "#00AA00"
    warning: str = "orange"
    muted: str = "gray"


@dataclass(frozen=True)
class SpacingStyle:
    paragraph_mm: float = 2.0
    section_mm: float = 6.0
    table_mm: float = 4.0
    figure_mm: float = 4.0


@dataclass(frozen=True)
class ReportTheme:
    """Immutable formatting source.  Constructed once; never modified."""

    page: PageGeometry = field(default_factory=PageGeometry)
    typography: TypographyStyle = field(default_factory=TypographyStyle)
    colors: ColorPalette = field(default_factory=ColorPalette)
    spacing: SpacingStyle = field(default_factory=SpacingStyle)
    
    table_styles: Dict[str, TableStyle] = field(default_factory=lambda: {
        "default": TableStyle(),
        "compact": TableStyle(column_padding_pt=4, row_height_factor=1.0, font_size="small"),
        "load": TableStyle(column_padding_pt=5, row_height_factor=1.1, font_size="small"),
        "detailed": TableStyle(column_padding_pt=4, row_height_factor=1.1, font_size="small"),
        "summary": TableStyle(column_padding_pt=6, row_height_factor=1.2, font_size="normalsize"),
    })
    
    charts: Dict[str, ChartStyle] = field(default_factory=lambda: {
        "default": ChartStyle(),
        "summary": ChartStyle(width_cm=10, height_cm=6, title_font_size=10, annotation_font_size=8),
    })
