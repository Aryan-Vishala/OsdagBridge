# =============================================================================
# Chapter 2: Input Parameters — document builder.
#
# First real migration — Project Location table is a semantic Table component.
# All other tables remain as RawLatex from the legacy function until they are
# individually migrated.
# =============================================================================

import re
from typing import List, Tuple

from ..document import Chapter, Column, RawLatex, Section, Table
from ..facts import ReportFacts
from ..layout import LayoutHints


def build_chapter_2(facts: ReportFacts) -> Chapter:
    """Build Chapter 2: Input Parameters.

    Project Location and Bridge Geometry tables are semantic Table components.
    Everything else is delegated to the legacy ``ch2_input_parameters()``
    function via ``RawLatex``.
    """
    from osdagbridge.core.reports.chap2 import ch2_input_parameters

    m = _MetadataProxy(facts.metadata.project_location)
    legacy_latex = ch2_input_parameters(m, facts.raw_input_dict or {}, facts.raw_output_dict)

    # --- Strip chapter heading and migrated tables from legacy ---
    remaining = _strip_project_location_table(legacy_latex)
    remaining = _strip_bridge_geometry_table(remaining)
    remaining = _strip_material_selection_table(remaining)
    remaining = _strip_typical_section_table(remaining)
    remaining = _strip_components_details_table(remaining)
    remaining = _strip_shear_connector_table(remaining)
    remaining = _strip_safety_factors_table(remaining)
    remaining = _strip_chapter_heading(remaining).lstrip("\n")

    # --- Extract section heading from remaining text, remove it from RawLatex ---
    section_title, remaining_after_heading = _extract_first_section(remaining)

    # --- Extract section intro (before first \begin{table} or \begin{longtable}) ---
    idx_table = remaining_after_heading.find(r"\begin{table}")
    idx_longtable = remaining_after_heading.find(r"\begin{longtable}")
    if idx_table == -1 and idx_longtable == -1:
        idx = -1
    elif idx_table == -1:
        idx = idx_longtable
    elif idx_longtable == -1:
        idx = idx_table
    else:
        idx = min(idx_table, idx_longtable)
    section_intro = remaining_after_heading[:idx].rstrip() if idx != -1 else remaining_after_heading.rstrip()
    rest_of_tables = remaining_after_heading[idx:] if idx != -1 else ""

    # --- Build the semantic tables from facts ---
    pl_table = _build_project_location_table(facts)
    bg_table = _build_bridge_geometry_table(facts)
    ms_table = _build_material_selection_table(facts)
    ts_table = _build_typical_section_table(facts)
    cd_table = _build_components_details_table(facts)
    sc_table = _build_shear_connector_table(facts)
    sf_table = _build_safety_factors_table(facts)

    # --- Assemble: section intro → PL → BG → MS → TS → CD → SC → SF → legacy ---
    return Chapter(
        number=2,
        title="Input Parameters",
        sections=[
            Section(
                title=section_title,
                level=2,
                components=[
                    RawLatex(section_intro),
                    pl_table,
                    bg_table,
                    ms_table,
                    ts_table,
                    cd_table,
                    sc_table,
                    sf_table,
                    RawLatex(rest_of_tables),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# Semantic Project Location table
# ---------------------------------------------------------------------------

def _build_project_location_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Project Location from facts.

    Chapter builders describe data.  The renderer handles LaTeX escaping.
    """
    input_dict = facts.raw_input_dict or {}

    return Table(
        caption="Project Location",
        label="subsec:project-location",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="8.5cm"),
        ],
        rows=[
            ["Project Location", facts.metadata.project_location or ""],
            [
                "Latitude / Longitude",
                (input_dict.get("latitude") or "") + ", " + (input_dict.get("longitude") or ""),
            ],
            ["Seismic Zone (IRC 6)", input_dict.get("seismic_zone") or ""],
            ["Basic Wind Speed (IRC 6)", (input_dict.get("wind_speed") or "") + " m/s"],
            [
                "Shade Temp. Max / Min (IRC 6)",
                (input_dict.get("shade_temp_max") or "") + " °C / "
                + (input_dict.get("shade_temp_min") or "") + " °C",
            ],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Bridge Geometry table
# ---------------------------------------------------------------------------

def _build_bridge_geometry_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Bridge Geometry from facts."""
    input_dict = facts.raw_input_dict or {}

    def _val(key: str, unit: str = "") -> str:
        v = input_dict.get(key) or ""
        return (v + unit) if v else ""

    return Table(
        caption="Bridge Geometry",
        label="subsec:bridge-geometry",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="8.5cm"),
        ],
        rows=[
            ["Type of Structure", _val("structure.type")],
            ["Span (m)", _val("geometry.span", " m")],
            ["Carriageway Width (m)", _val("geometry.carriageway_width", " m")],
            ["Include Median", _val("geometry.include_median")],
            ["Footpath", _val("geometry.footpath")],
            [
                "Skew Angle (degrees)",
                _val("geometry.skew_angle", "°")
                + " (IRC 24 Cl. 504.8 limit: ±15°)",
            ],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Material Selection table
# ---------------------------------------------------------------------------

def _build_material_selection_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Material Selection from facts."""
    input_dict = facts.raw_input_dict or {}

    def _val(key: str) -> str:
        return input_dict.get(key) or ""

    return Table(
        caption="Material Selection",
        label="subsec:material",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="8.5cm"),
        ],
        rows=[
            ["Girder Steel Grade (IS 2062)", _val("material.girder")],
            ["Cross Bracing Steel Grade", _val("material.cross_bracing")],
            ["End Diaphragm Steel Grade", _val("material.end_diaphragm")],
            ["Concrete Deck Grade (IRC 22)", _val("material.deck")],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Typical Section Details table
# ---------------------------------------------------------------------------

def _build_typical_section_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Typical Section Details from facts."""
    input_dict = facts.raw_input_dict or {}

    def _val(key: str, unit: str = "") -> str:
        v = input_dict.get(key) or ""
        return (v + unit) if v else ""

    return Table(
        caption="Typical Section Details",
        label="",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="10.0cm"),
        ],
        rows=[
            ["Overall Bridge Width (m)", _val("typical_section.overall_bridge_width")],
            ["No. of Girders", _val("typical_section.no_of_girders")],
            ["Girder Spacing (m)", _val("typical_section.girder_spacing", " m")],
            ["Deck Overhang Width (m)", _val("typical_section.deck_overhang", " m")],
            ["Deck Thickness (mm)", _val("typical_section.deck_thickness", " mm")],
            [
                "Footpath Width (m)",
                _val("typical_section.footpath_width", " m")
                + (" (IRC 5 Cl. 104.3.6 min: 1.5 m)" if input_dict.get("typical_section.footpath_width") else ""),
            ],
            [
                "No. of Traffic Lanes",
                _val("typical_section.lane_details.lane_table_count")
                + (" (per IRC 5 Cl. 104.3.1)" if input_dict.get("typical_section.lane_details.lane_table_count") else ""),
            ],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Components Details table
# ---------------------------------------------------------------------------

def _build_components_details_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Components Details from facts.

    The Median Type row is conditional — only present when the user has
    enabled the median.
    """
    input_dict = facts.raw_input_dict or {}

    def _val(key: str, unit: str = "") -> str:
        v = input_dict.get(key) or ""
        return (v + unit) if v else ""

    # Conditional median row
    median_value = _val("typical_section.median.type")
    median_row = ["Median Type", median_value] if median_value else None

    rows: list = [
        ["Crash Barrier Type", _val("typical_section.crash_barrier.type")],
        ["Crash Barrier Load (kN/m)", _val("typical_section.crash_barrier.load")],
    ]
    if median_row:
        rows.append(median_row)
    rows += [
        ["Railing Type", _val("typical_section.railing.type")],
        ["Railing Load (kN/m)", _val("typical_section.railing.load_value")],
        ["Wearing Course Material", _val("typical_section.wearing_course.material")],
        ["Wearing Course Thickness (mm)", _val("typical_section.wearing_course.thickness", " mm")],
    ]

    return Table(
        caption="Components Details",
        label="",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="10.0cm"),
        ],
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Shear Connector Details table
# ---------------------------------------------------------------------------

def _build_shear_connector_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Shear Connector Details from facts.

    Values come from ``raw_output_dict`` (populated by design results).
    """
    od = facts.raw_output_dict or {}

    def _val(key: str, unit: str = "") -> str:
        v = od.get(key) or ""
        return (v + unit) if v else ""

    return Table(
        caption="Shear Connector Details",
        label="subsec:shear-connectors",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="10.0cm"),
        ],
        rows=[
            ["Stud Diameter (mm)", _val("steeldesign.details.shear.diameter", " mm")],
            ["Stud Height (mm)", _val("steeldesign.details.shear.height", " mm")],
            ["Stud $f_y$ (MPa)", _val("steeldesign.details.shear.yield_strength", " MPa")],
            ["Stud $f_u$ (MPa)", _val("steeldesign.details.shear.ultimate_strength", " MPa")],
            ["No. of Studs per Section", _val("steeldesign.details.shear.studs_per_section")],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Partial Safety Factors table
# ---------------------------------------------------------------------------

def _build_safety_factors_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Partial Safety Factors from facts."""
    input_dict = facts.raw_input_dict or {}

    def _val(key: str) -> str:
        return input_dict.get(key) or ""

    return Table(
        caption="Partial Safety Factors",
        label="subsec:safety-factors",
        columns=[
            Column("Parameter", width="5.5cm"),
            Column("Value", width="10.0cm"),
        ],
        rows=[
            [r"$\gamma_{M0}$ (Yielding / Buckling)", _val("design_options_cont.partial_factor.yielding_and_buckling.gamma_m0")],
            [r"$\gamma_{M1}$ (Ultimate Stress)", _val("design_options_cont.partial_factor.ultimate_stress.gamma_m1")],
            [r"$\gamma_C$ (Concrete, Basic)", _val("design_options_cont.partial_factor.concrete_basic.gamma_c_basic")],
            [r"$\gamma_s$ (Reinforcement)", _val("design_options_cont.partial_factor.reinforcing_steel.gamma_s")],
            [r"$\gamma_v$ (Shear Connectors)", _val("design_options_cont.partial_factor.shear_connectors.gamma_v")],
            [r"$\gamma_{fft}$ (Fatigue Load)", _val("design_options_cont.partial_factor.fatigue_load.gamma_flt")],
            [r"$\gamma_{Mft}$ (Fatigue Strength)", _val("design_options_cont.partial_factor.fatigue_strength.gamma_mf")],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Legacy output manipulation
# ---------------------------------------------------------------------------

_RE_PL_TABLE = re.compile(
    r"\n\\begin\{table\}\[H\]\n"
    r"\\caption\{\\textbf\{Project Location\}\}.*?"
    r"\\end\{table\}",
    re.DOTALL,
)

_RE_BG_TABLE = re.compile(
    r"\n\\begin\{table\}\[H\]\n"
    r"\\caption\{\\textbf\{Bridge Geometry\}\}.*?"
    r"\\end\{table\}",
    re.DOTALL,
)

_RE_MS_TABLE = re.compile(
    r"\n\\begin\{table\}\[H\]\n"
    r"\\caption\{\\textbf\{Material Selection\}\}.*?"
    r"\\end\{table\}",
    re.DOTALL,
)

_RE_TS_TABLE = re.compile(
    r"\n\\begin\{longtable\}\{[^}]*\}\n"
    r"\\caption\{\\textbf\{Typical Section Details\}\}.*?"
    r"\\end\{longtable\}",
    re.DOTALL,
)

_RE_CD_TABLE = re.compile(
    r"\n\\begin\{longtable\}\{[^}]*\}\n"
    r"\\caption\{\\textbf\{Components Details\}\}.*?"
    r"\\end\{longtable\}",
    re.DOTALL,
)

_RE_SC_TABLE = re.compile(
    r"\n\\begin\{longtable\}\{[^}]*\}\n"
    r"\\caption\{\\textbf\{Shear Connector Details\}\}.*?"
    r"\\end\{longtable\}",
    re.DOTALL,
)

_RE_SF_TABLE = re.compile(
    r"\n\\begin\{longtable\}\{[^}]*\}\n"
    r"\\caption\{\\textbf\{Partial Safety Factors\}\}.*?"
    r"\\end\{longtable\}",
    re.DOTALL,
)

_RE_CHAPTER_HEADING = re.compile(
    r"\\chapter\{[^}]*\}\s*",
)


def _strip_project_location_table(latex: str) -> str:
    """Remove the Project Location ``\\begin{table}...\\end{table}`` block."""
    return _RE_PL_TABLE.sub("", latex)


def _strip_bridge_geometry_table(latex: str) -> str:
    """Remove the Bridge Geometry ``\\begin{table}...\\end{table}`` block."""
    return _RE_BG_TABLE.sub("", latex)


def _strip_material_selection_table(latex: str) -> str:
    """Remove the Material Selection ``\\begin{table}...\\end{table}`` block."""
    return _RE_MS_TABLE.sub("", latex)


def _strip_typical_section_table(latex: str) -> str:
    """Remove the Typical Section Details ``\\begin{longtable}...\\end{longtable}`` block."""
    return _RE_TS_TABLE.sub("", latex)


def _strip_components_details_table(latex: str) -> str:
    """Remove the Components Details ``\\begin{longtable}...\\end{longtable}`` block."""
    return _RE_CD_TABLE.sub("", latex)


def _strip_shear_connector_table(latex: str) -> str:
    """Remove the Shear Connector Details ``\\begin{longtable}...\\end{longtable}`` block."""
    return _RE_SC_TABLE.sub("", latex)


def _strip_safety_factors_table(latex: str) -> str:
    """Remove the Partial Safety Factors ``\\begin{longtable}...\\end{longtable}`` block."""
    return _RE_SF_TABLE.sub("", latex)


def _strip_chapter_heading(latex: str) -> str:
    """Remove the ``\\chapter{...}`` line from legacy output."""
    return _RE_CHAPTER_HEADING.sub("", latex, count=1)


_RE_SECTION_HEADING = re.compile(
    r"\\section\{([^}]*)\}\s*\\label\{[^}]*\}\s*",
    re.DOTALL,
)


def _extract_first_section(latex: str) -> tuple:
    """Extract the first ``\\section{...}`` title and remove it from ``latex``.

    Returns ``(section_title, latex_without_heading)``.
    If no section heading is found, returns ``("", latex)``.
    """
    m = _RE_SECTION_HEADING.search(latex)
    if not m:
        return ("", latex)
    return (m.group(1), latex[m.end():])


class _MetadataProxy:
    """Minimal proxy for the ``ReportMetadata`` interface used by
    ``ch2_input_parameters()``."""
    def __init__(self, project_location: str = ""):
        self.project_location = project_location
