"""OsdagBridge Report Engine — structured, validated report generation.

Architecture::

    ReportFacts → ReportDocument → LatexRenderer → PDF → PDFPreflight
"""

from .facts import (
    CheckStatus,
    DeadLoadFact,
    DesignCheckData,
    FactMetadata,
    FootwayLoadFact,
    GirderClassification,
    GirderDeflectionCheck,
    GirderDesignData,
    GirderDesignSummary,
    GirderFatigueCheck,
    GirderFlexureCheck,
    GirderInteractionCheck,
    GirderLTBCheck,
    GirderSectionProperties,
    GirderShearCheck,
    GirderStiffenerSummary,
    GirderStressCheck,
    GirderBearingStiffenerCheck,
    GirderIntermediateStiffenerCheck,
    InputFacts,
    LiveLoadFact,
    LoadCombinationFact,
    LoadFacts,
    MaterialFacts,
    MaterialQuantityFact,
    QuantityValue,
    ReportFacts,
    SeismicLoadFact,
    SurfacingLoadFact,
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
    TableGroup,
)
from .facts.design_checks import build_girder_design_data
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
from .manifest import (
    ChapterManifest,
    ChapterParity,
    ParityItem,
    ParityReport,
    ParityStatus,
    ReportManifest,
    SectionManifest,
    TableManifest,
    compare_manifests,
    extract_legacy_manifest,
    extract_legacy_manifest_from_payload,
    extract_semantic_manifest,
)
from .provenance import (
    FactProvenance,
    ProvenanceTracker,
    ProvenanceValidationIssue,
    ValueSource,
)
from .validation import (
    ValidationIssue,
    ValidationReport,
    validate_facts,
    validate_payload,
)

__all__ = [
    # Facts
    "QuantityValue",
    "ReportFacts",
    "FactMetadata",
    "DeadLoadFact",
    "SurfacingLoadFact",
    "VehicleLiveLoadFact",
    "FootwayLoadFact",
    "LiveLoadFact",
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
    "TableGroup",
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
    # Manifest
    "ParityStatus",
    "TableManifest",
    "SectionManifest",
    "ChapterManifest",
    "ReportManifest",
    "ParityItem",
    "ChapterParity",
    "ParityReport",
    "extract_semantic_manifest",
    "extract_legacy_manifest",
    "extract_legacy_manifest_from_payload",
    "compare_manifests",
    # Provenance
    "ValueSource",
    "FactProvenance",
    "ProvenanceValidationIssue",
    "ProvenanceTracker",
    # Validation
    "ValidationIssue",
    "ValidationReport",
    "validate_payload",
    "validate_facts",
]
