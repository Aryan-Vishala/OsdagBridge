"""OsdagBridge Report Engine — structured, validated report generation.

Architecture::

    ReportFacts → ReportDocument → LatexRenderer → PDF → PDFPreflight
"""

from .facts import (
    DeadLoadFact,
    FactMetadata,
    FootwayLoadFact,
    InputFacts,
    LoadCombinationFact,
    LoadFacts,
    MaterialFacts,
    MaterialQuantityFact,
    QuantityValue,
    ReportFacts,
    SeismicLoadFact,
    TemperatureLoadFact,
    UtilizationFact,
    UtilizationFacts,
    VehicleLiveLoadFact,
    WindLoadFact,
)
from .document import (
    Callout,
    Chart,
    Chapter,
    Column,
    Figure,
    RawLatex,
    ReportDocument,
    Section,
    Table,
)
from .layout import LayoutHints
from .theme import (
    ChartStyle,
    ColorPalette,
    PageGeometry,
    ReportTheme,
    TableStyle,
    TypographyStyle,
)
from .renderer import LatexRenderer
from .preflight import PDFPreflight, PreflightReport, PreflightStatus
from .document_builder import build_report_document

__all__ = [
    # Facts
    "QuantityValue",
    "ReportFacts",
    "FactMetadata",
    "DeadLoadFact",
    "VehicleLiveLoadFact",
    "FootwayLoadFact",
    "WindLoadFact",
    "SeismicLoadFact",
    "TemperatureLoadFact",
    "LoadCombinationFact",
    "LoadFacts",
    "UtilizationFact",
    "UtilizationFacts",
    "MaterialQuantityFact",
    "MaterialFacts",
    "InputFacts",
    # Document
    "ReportDocument",
    "Chapter",
    "Section",
    "Column",
    "Table",
    "Chart",
    "Figure",
    "Callout",
    "RawLatex",
    # Layout
    "LayoutHints",
    # Theme
    "ReportTheme",
    "PageGeometry",
    "TableStyle",
    "ChartStyle",
    "TypographyStyle",
    "ColorPalette",
    # Renderer
    "LatexRenderer",
    # Preflight
    "PDFPreflight",
    "PreflightReport",
    "PreflightStatus",
    # Builder
    "build_report_document",
]
