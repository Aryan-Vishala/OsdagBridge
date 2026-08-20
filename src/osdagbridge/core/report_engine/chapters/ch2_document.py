# =============================================================================
# Chapter 2: Input Parameters — document builder.
#
# First real migration — Project Location table is a semantic Table component.
# All other tables remain as RawLatex from the legacy function until they are
# individually migrated.
# =============================================================================

import re
from typing import List, Tuple

from osdagbridge.core.report_engine.document import Chapter, Column, LayoutHints, RawLatex, Section, Table, TableGroup, Math, Paragraph
from ..facts import ReportFacts
from ..layout import LayoutHints


def build_chapter_2(facts: ReportFacts) -> Chapter:
    """Build Chapter 2: Input Parameters purely from semantic components."""

    # --- Build the semantic tables from facts ---
    pl_table = _build_project_location_table(facts)
    bg_table = _build_bridge_geometry_table(facts)
    ms_table = _build_material_selection_table(facts)
    ts_table = _build_typical_section_table(facts)
    cd_table = _build_components_details_table(facts)
    ggi_table = _build_girder_general_info_table(facts)
    gsd_table = _build_girder_section_details_table(facts)
    grs_table = _build_girder_restraint_stiffener_table(facts)
    cbd_table = _build_cross_bracing_details_table(facts)
    edd_table = _build_end_diaphragm_details_table(facts)
    sc_table = _build_shear_connector_table(facts)
    sf_table = _build_safety_factors_table(facts)

    return Chapter(
        number=2,
        title="Input Parameters",
        sections=[
            Section(
                title="",
                level=2,
                components=[
                    Paragraph(
                        "This section documents all inputs provided to OsdagBridge. User-provided inputs are "
                        "clearly distinguished from software-assumed defaults. Where the user did not supply a "
                        "value, the software has applied the IRC/IS code default or an empirical guideline; these "
                        "are annotated with an asterisk (*)."
                    ),
                ],
            ),
            Section(
                title="Basic Inputs (User-Defined)",
                level=2,
                components=[
                    Paragraph("Note: These inputs are mandatory and were provided by the user."),
                    pl_table,
                    bg_table,
                    ms_table,
                ],
            ),
            Section(
                title="Additional Inputs",
                level=2,
                components=[
                    Paragraph(
                        "Where the user has modified additional inputs, those values are reported here. "
                        "Where no modification was made, the software default is shown."
                    ),
                    ts_table,
                    cd_table,
                    ggi_table,
                    gsd_table,
                    grs_table,
                    cbd_table,
                    edd_table,
                    sc_table,
                    sf_table,
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
    weather = facts.inputs.weather if facts.inputs else {}
    raw_in = facts.raw_input_dict or {}

    def _val(key: str, unit: str = "") -> str:
        if key in raw_in and raw_in[key] not in (None, ""):
            raw_val = raw_in[key]
            val_str = str(raw_val)
            return f"{val_str}{unit}".strip()
        v = weather.get(key)
        if v and v.value not in (None, ""):
            val_str = str(v.value)
            return f"{val_str}{unit}".strip()
        return ""

    lat = _val("latitude")
    lon = _val("longitude")
    lat_lon = f"{lat}, {lon}" if lat and lon else (lat or lon)
    
    t_max = _val("shade_temp_max", " °C")
    t_min = _val("shade_temp_min", " °C")
    shade_temp = f"{t_max} / {t_min}" if t_max and t_min else (t_max or t_min)

    return Table(
        caption="Project Location",
        label="subsec:project-location",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="L{8.5cm}"),
        ],
        rows=[
            ["Project Location", facts.metadata.project_location or ""],
            ["Latitude / Longitude", lat_lon],
            ["Seismic Zone (IRC 6)", _val("seismic_zone")],
            ["Basic Wind Speed (IRC 6)", _val("wind_speed", " m/s")],
            ["Shade Temp. Max / Min (IRC 6)", shade_temp],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Bridge Geometry table
# ---------------------------------------------------------------------------

def _build_bridge_geometry_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Bridge Geometry from facts."""
    geom = facts.inputs.geometry if facts.inputs else {}
    raw_in = facts.raw_input_dict or {}

    def _val(key: str, unit: str = "") -> str:
        for candidate in (f"geometry.{key}", f"structure.{key}", key):
            if candidate in raw_in and raw_in[candidate] not in (None, ""):
                raw_val = raw_in[candidate]
                val_str = str(raw_val)
                return f"{val_str}{unit}".strip()
        v = geom.get(key)
        if not v or v.value in (None, ""):
            return ""
        val_str = f"{v.value:g}" if isinstance(v.value, (int, float)) else str(v.value)
        return f"{val_str}{unit}".strip()

    skew = _val("skew_angle", "°") or "0°"
    skew_cell = [
        skew,
        " (IRC 24 Cl. 504.8 limit: ",
        Math(r"\pm"),
        "15",
        Math(r"^\circ"),
        ")",
    ]

    return Table(
        caption="Bridge Geometry",
        label="subsec:bridge-geometry",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="p{8.5cm}"),
        ],
        rows=[
            ["Type of Structure", _val("structure.type") or _val("type") or _val("structure_type")],
            ["Span (m)", _val("span", " m")],
            ["Carriageway Width (m)", _val("carriageway_width", " m")],
            ["Include Median", _val("include_median")],
            ["Footpath", _val("footpath")],
            ["Skew Angle (degrees)", skew_cell],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Material Selection table
# ---------------------------------------------------------------------------

def _build_material_selection_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Material Selection from facts."""
    mat = facts.inputs.material if facts.inputs else {}
    raw_in = facts.raw_input_dict or {}

    def _val(key: str) -> str:
        for candidate in (f"material.{key}", f"material.{key}.steel_grade", f"material.{key}.concrete_grade", key):
            if candidate in raw_in and raw_in[candidate] not in (None, ""):
                return str(raw_in[candidate])
        v = mat.get(key)
        if v and v.value not in (None, ""):
            return str(v.value)
        return ""

    return Table(
        caption="Material Selection",
        label="subsec:material",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="L{8.5cm}"),
        ],
        rows=[
            ["Girder Steel Grade (IS 2062)", _val("girder")],
            ["Cross Bracing Steel Grade", _val("cross_bracing")],
            ["End Diaphragm Steel Grade", _val("end_diaphragm")],
            ["Concrete Deck Grade (IRC 22)", _val("deck")],
        ],
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Typical Section Details table
# ---------------------------------------------------------------------------

def _build_typical_section_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Typical Section Details from facts."""
    sec = facts.inputs.section if (facts.inputs and hasattr(facts.inputs, "section")) else {}
    input_dict = facts.raw_input_dict or {}

    def _val(key: str) -> str:
        if isinstance(sec, dict):
            v = sec.get(key)
            if v and v.value is not None:
                return f"{v.value:g} {v.unit}".strip()
        raw_key = f"typical_section.{key}"
        if raw_key in input_dict and input_dict[raw_key] not in (None, ""):
            v_raw = input_dict[raw_key]
            unit = " mm" if "thickness" in key else (" m" if "width" in key or "spacing" in key or "overhang" in key else "")
            return f"{v_raw}{unit}".strip()
        return ""

    def _raw_val(key: str) -> str:
        v = input_dict.get(key)
        return str(v) if v not in (None, "") else ""

    cw_raw = input_dict.get("geometry.carriageway_width") or input_dict.get("carriageway_width") or 0
    try:
        cw_val = float(cw_raw)
        est_lanes = max(1, int(cw_val / 3.5)) if cw_val > 0 else 2
    except Exception:
        est_lanes = 2
    lanes_val = str(input_dict.get("typical_section.lane_details.lane_table_count") or input_dict.get("num_lanes") or est_lanes)

    return Table(
        caption="Typical Section Details",
        label="subsec:typical-section",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="p{10.0cm}"),
        ],
        rows=[
            ["Overall Bridge Width (m)", _val("overall_bridge_width")],
            ["No. of Girders", _raw_val("typical_section.no_of_girders")],
            ["Girder Spacing (m)", _val("girder_spacing")],
            ["Deck Overhang Width (m)", _val("deck_overhang")],
            ["Deck Thickness (mm)", _val("deck_thickness")],
            [
                "Footpath Width (m)",
                _val("footpath_width")
                + (" (IRC 5 Cl. 104.3.6 min: 1.5 m)" if input_dict.get("typical_section.footpath_width") else ""),
            ],
            [
                "No. of Traffic Lanes",
                f"{lanes_val} (per IRC 5 Cl. 104.3.1)",
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
        v = input_dict.get(key)
        if v in (None, ""):
            return ""
        return f"{v}{unit}"

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
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="p{10.0cm}"),
        ],
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Girder General Information table (Table 2.6)
# ---------------------------------------------------------------------------

def _build_girder_general_info_table(facts: ReportFacts) -> Table:
    """Build Table 2.6: Girder General Information from facts."""
    from osdagbridge.core.reports.report_utils import get_girder_entries
    input_dict = facts.raw_input_dict or {}
    girder_entries = get_girder_entries(input_dict)
    n = len(girder_entries) if girder_entries else int(input_dict.get("typical_section.no_of_girders", 1) or 1)
    if not girder_entries:
        girder_entries = [(f"G{i}", f"G{i}M1") for i in range(1, n + 1)]

    design_mode = str(input_dict.get("design_options_cont.design_mode", "Custom")).capitalize()

    cols = [
        Column("Girder", width="C{1.8cm}"),
        Column("Member ID", width="C{2.5cm}"),
        Column("Design Mode", width="C{3.0cm}"),
        Column("Girder Type", width="C{3.0cm}"),
        Column("Girder Symmetry", width="C{4.0cm}"),
    ]
    rows = []
    for i, (lbl, mid) in enumerate(girder_entries, start=1):
        g_type = input_dict.get(f"member_properties.girder.girder_type.G{i}.M1", "Welded")
        g_symm = input_dict.get(f"member_properties.girder.girder_symmetry.G{i}.M1", "Girder Symmetric")
        rows.append([lbl, mid, design_mode, g_type, g_symm])

    return Table(
        caption="Girder General Information",
        label="subsec:girder-general-info",
        columns=cols,
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Girder Section Dimensions table (Table 2.7)
# ---------------------------------------------------------------------------

def _build_girder_section_details_table(facts: ReportFacts) -> Table:
    """Build Table 2.7: Girder Section Dimensions with full baseline headers."""
    from osdagbridge.core.reports.report_utils import get_girder_entries
    input_dict = facts.raw_input_dict or {}
    girder_entries = get_girder_entries(input_dict)
    n = len(girder_entries) if girder_entries else int(input_dict.get("typical_section.no_of_girders", 1) or 1)
    if not girder_entries:
        girder_entries = [(f"G{i}", f"G{i}M1") for i in range(1, n + 1)]

    cols = [
        Column("Girder", width="C{1.5cm}"),
        Column("Total Depth, D (mm)", width="C{3.2cm}"),
        Column(["Web, ", Math(r"t_w"), " (mm)"], width="C{2.5cm}"),
        Column(["Top Flange (", Math(r"b_{tf}"), ", ", Math(r"t_{tf}"), ") mm"], width="C{4.0cm}"),
        Column(["Bottom Flange (", Math(r"b_{bf}"), ", ", Math(r"t_{bf}"), ") mm"], width="C{4.0cm}"),
    ]

    def _conv_dim(val):
        if val is None or val == "":
            return "---"
        try:
            v = float(val)
            if 0 < v < 10:
                v *= 1000.0
            return f"{v:g} mm"
        except (ValueError, TypeError):
            return f"{val} mm"

    rows = []
    for i, (lbl, _) in enumerate(girder_entries, start=1):
        d = input_dict.get(f"member_properties.girder.depth.G{i}.M1")
        tw = input_dict.get(f"member_properties.girder.web_thickness.G{i}.M1")
        bf_top = input_dict.get(f"member_properties.girder.top_flange_width.G{i}.M1")
        tf_top = input_dict.get(f"member_properties.girder.top_flange_thickness.G{i}.M1")
        bf_bot = input_dict.get(f"member_properties.girder.bottom_flange_width.G{i}.M1")
        tf_bot = input_dict.get(f"member_properties.girder.bottom_flange_thickness.G{i}.M1")

        if (d is None or tw is None) and facts.design_check_data and facts.design_check_data.girders:
            for g in facts.design_check_data.girders:
                if g.girder_label == lbl:
                    sp = g.section_properties
                    d = sp.depth.value if sp.depth else d
                    tw = sp.web_thickness.value if sp.web_thickness else tw
                    bf_top = sp.top_flange_width.value if sp.top_flange_width else bf_top
                    tf_top = sp.top_flange_thickness.value if sp.top_flange_thickness else tf_top
                    bf_bot = sp.bottom_flange_width.value if sp.bottom_flange_width else bf_bot
                    tf_bot = sp.bottom_flange_thickness.value if sp.bottom_flange_thickness else tf_bot
                    break

        if (d is None or tw is None) and facts.raw_output_dict:
            od = facts.raw_output_dict
            idx = i - 1
            d = od.get(f"steeldesign.girders.[{idx}].section.web_depth", d)
            tw = od.get(f"steeldesign.girders.[{idx}].section.web_thickness", tw)
            bf_top = od.get(f"steeldesign.girders.[{idx}].section.top_flange_width", bf_top)
            tf_top = od.get(f"steeldesign.girders.[{idx}].section.top_flange_thickness", tf_top)
            bf_bot = od.get(f"steeldesign.girders.[{idx}].section.bot_flange_width", bf_bot)
            tf_bot = od.get(f"steeldesign.girders.[{idx}].section.bot_flange_thickness", tf_bot)

        d_str = _conv_dim(d)
        tw_str = _conv_dim(tw)
        top_str = f"{_conv_dim(bf_top)}, {_conv_dim(tf_top)}" if bf_top and tf_top else "---"
        bot_str = f"{_conv_dim(bf_bot)}, {_conv_dim(tf_bot)}" if bf_bot and tf_bot else "---"
        rows.append([lbl, d_str, tw_str, top_str, bot_str])

    return Table(
        caption="Girder Section Dimensions",
        label="subsec:girder-section-dimensions",
        columns=cols,
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Girder Restraint and Stiffener Details table (Table 2.8)
# ---------------------------------------------------------------------------

def _build_girder_restraint_stiffener_table(facts: ReportFacts) -> Table:
    """Build Table 2.8: Girder Restraint and Stiffener Details."""
    from osdagbridge.core.reports.report_utils import get_girder_entries
    input_dict = facts.raw_input_dict or {}
    girder_entries = get_girder_entries(input_dict)
    n = len(girder_entries) if girder_entries else int(input_dict.get("typical_section.no_of_girders", 1) or 1)
    if not girder_entries:
        girder_entries = [(f"G{i}", f"G{i}M1") for i in range(1, n + 1)]

    cols = [
        Column("Girder", width="C{1.5cm}"),
        Column("Torsional / Warping Restraint", width="L{3.0cm}"),
        Column("Web Philosophy", width="L{2.5cm}"),
        Column("Intermediate Stiffeners", width="L{3.2cm}"),
        Column("Longitudinal Stiffeners", width="L{2.5cm}"),
        Column("Bearing Stiffener", width="L{3.0cm}"),
    ]
    rows = []
    for i, (lbl, _) in enumerate(girder_entries, start=1):
        tors = (
            input_dict.get(f"member_properties.girder_details.section_input.torsional_restraint.G{i}.M1")
            or input_dict.get(f"member_properties.girder.torsional_restraint.G{i}.M1")
            or "Fully Restrained"
        )
        warp = (
            input_dict.get(f"member_properties.girder_details.section_input.warping_restraint.G{i}.M1")
            or input_dict.get(f"member_properties.girder.warping_restraint.G{i}.M1")
            or "Both Flanges Restrained"
        )
        restraint_str = f"{tors}, {warp}" if tors and warp else (tors or warp or "---")

        web_phil = (
            input_dict.get(f"member_properties.girder_details.section_input.web_type.G{i}.M1")
            or input_dict.get(f"member_properties.girder.web_type.G{i}.M1")
            or "Thin Web with ITS"
        )

        int_stiff = (
            input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener")
            or input_dict.get(f"member_properties.stiffener.intermediate.G{i}.M1")
            or "Yes"
        )
        int_sp = (
            input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener_spacing.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener_spacing")
            or input_dict.get(f"member_properties.stiffener.intermediate_spacing.G{i}.M1")
            or ""
        )
        int_thk = (
            input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener_thickness.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.intermediate_stiffener_thickness")
            or input_dict.get(f"member_properties.stiffener.intermediate_thickness.G{i}.M1")
            or ""
        )
        if int_stiff and str(int_stiff).lower() in ("yes", "true", "1"):
            int_str = f"Yes; Spacing: {int_sp} mm; Thickness: {int_thk} mm" if int_sp and int_thk else "Yes"
        else:
            int_str = "No"

        long_stiff = (
            input_dict.get(f"member_properties.stiffener_details.longitudinal_stiffener.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.longitudinal_stiffener")
            or input_dict.get(f"member_properties.stiffener.longitudinal.G{i}.M1")
            or "No"
        )
        if str(long_stiff).lower() in ("no", "none", "false", "0"):
            long_str = "No"
        else:
            long_thk = (
                input_dict.get(f"member_properties.stiffener_details.longitudinal_stiffener_thickness.G{i}.M1")
                or input_dict.get(f"member_properties.stiffener_details.longitudinal_stiffener_thickness")
                or ""
            )
            long_str = f"Yes; Thickness: {long_thk} mm" if long_thk else "Yes"

        brg_no = (
            input_dict.get(f"member_properties.stiffener_details.no_bearing_stiffeners_each_end.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.no_bearing_stiffeners_each_end")
            or input_dict.get(f"member_properties.stiffener.no_bearing_stiffeners.G{i}.M1")
            or ""
        )
        brg_sp = (
            input_dict.get(f"member_properties.stiffener_details.bearing_stiffener_spacing.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.bearing_stiffener_spacing")
            or input_dict.get(f"member_properties.stiffener.spacing.G{i}.M1")
            or ""
        )
        brg_thk = (
            input_dict.get(f"member_properties.stiffener_details.bearing_stiffener_plate_thickness.G{i}.M1")
            or input_dict.get(f"member_properties.stiffener_details.bearing_stiffener_plate_thickness")
            or input_dict.get(f"member_properties.stiffener.bearing_thickness.G{i}.M1")
            or ""
        )
        if brg_no not in (None, ""):
            brg_str = f"No.: {brg_no}; Spacing: {brg_sp} mm; Thickness: {brg_thk} mm"
        else:
            brg_str = "---"

        rows.append([lbl, restraint_str, web_phil, int_str, long_str, brg_str])

    return Table(
        caption="Girder Restraint and Stiffener Details",
        label="subsec:girder-restraint-stiffeners",
        columns=cols,
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Cross Bracing Details table (Table 2.9)
# ---------------------------------------------------------------------------

def _build_cross_bracing_details_table(facts: ReportFacts) -> Table:
    """Build Table 2.9: Member Properties: Cross Bracing Details."""
    from osdagbridge.core.reports.report_utils import get_girder_entries
    input_dict = facts.raw_input_dict or {}
    girder_entries = get_girder_entries(input_dict)
    n = len(girder_entries) if girder_entries else int(input_dict.get("typical_section.no_of_girders", 2) or 2)

    cols = [
        Column("Location", width="C{2.5cm}"),
        Column("Member IDs", width="C{2.5cm}"),
        Column("Type of Bracing", width="C{3.0cm}"),
        Column("Bracing Section", width="C{3.5cm}"),
        Column("Spacing (m)", width="C{2.5cm}"),
    ]
    rows = []
    for i in range(1, max(2, n)):
        loc = f"G{i} to G{i+1}"
        mids = (
            input_dict.get(f"member_properties.cross_bracing_details.member_id.G{i}G{i+1}.B{i}M1")
            or f"B{i}M1 to B{i}M1"
        )
        b_type = (
            input_dict.get(f"member_properties.cross_bracing_details.type.G{i}G{i+1}.B{i}M1")
            or input_dict.get(f"member_properties.cross_bracing.type.G{i}G{i+1}.B{i}M1")
            or "X-Bracing"
        )
        b_sec = (
            input_dict.get(f"member_properties.cross_bracing_details.bracing_section_designation.G{i}G{i+1}.B{i}M1")
            or input_dict.get(f"member_properties.cross_bracing_details.bracing_section_designation")
            or input_dict.get(f"member_properties.cross_bracing.bracing_section_designation.G{i}G{i+1}.B{i}M1")
            or ""
        )
        b_sp = (
            input_dict.get(f"member_properties.cross_bracing_details.spacing.G{i}G{i+1}.B{i}M1")
            or input_dict.get(f"member_properties.cross_bracing_details.spacing")
            or input_dict.get(f"member_properties.cross_bracing.spacing.G{i}G{i+1}.B{i}M1")
            or ""
        )
        sp_str = f"{b_sp} m" if b_sp not in (None, "", "---") else "---"
        rows.append([loc, mids, b_type, b_sec or "---", sp_str])

    return Table(
        caption="Member Properties: Cross Bracing Details",
        label="subsec:cross-bracing-details",
        columns=cols,
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic End Diaphragm Details table (Table 2.10)
# ---------------------------------------------------------------------------

def _build_end_diaphragm_details_table(facts: ReportFacts) -> Table:
    """Build Table 2.10: Member Properties: End Diaphragm Details."""
    from osdagbridge.core.reports.report_utils import get_girder_entries
    input_dict = facts.raw_input_dict or {}
    girder_entries = get_girder_entries(input_dict)
    n = len(girder_entries) if girder_entries else int(input_dict.get("typical_section.no_of_girders", 2) or 2)

    cols = [
        Column("Location", width="C{2.5cm}"),
        Column("Member IDs", width="C{2.5cm}"),
        Column("Type of Bracing", width="C{3.5cm}"),
        Column("Bracing Section", width="C{4.0cm}"),
    ]
    rows = []
    for i in range(1, max(2, n)):
        loc = f"G{i} to G{i+1}"
        mids = (
            input_dict.get(f"member_properties.end_diaphragm_details.member_id.G{i}G{i+1}.E{i}M1")
            or f"E{i}M1 to E{i}M2"
        )
        e_type = (
            input_dict.get(f"member_properties.end_diaphragm_details.type.G{i}G{i+1}.E{i}M1")
            or input_dict.get(f"member_properties.end_diaphragm_details.bracing_type.G{i}G{i+1}.E{i}M1")
            or input_dict.get(f"member_properties.end_diaphragm.type.G{i}G{i+1}.E{i}M1")
            or "Cross Bracing"
        )
        e_sec = (
            input_dict.get(f"member_properties.end_diaphragm_details.bracing_section_designation.G{i}G{i+1}.E{i}M1")
            or input_dict.get(f"member_properties.end_diaphragm_details.bottom_chord_section_designation.G{i}G{i+1}.E{i}M1")
            or input_dict.get(f"member_properties.end_diaphragm_details.bracing_section_designation")
            or input_dict.get(f"member_properties.end_diaphragm.bracing_section_designation.G{i}G{i+1}.E{i}M1")
            or ""
        )
        rows.append([loc, mids, e_type, e_sec or "---"])

    return Table(
        caption="Member Properties: End Diaphragm Details",
        label="subsec:end-diaphragm-details",
        columns=cols,
        rows=rows,
        layout=LayoutHints(space_after_mm=4),
    )


# ---------------------------------------------------------------------------
# Semantic Shear Connector Details table (Table 2.11)
# ---------------------------------------------------------------------------

def _build_shear_connector_table(facts: ReportFacts) -> Table:
    """Build Table 2.11: Shear Connector Details from facts."""
    od = facts.raw_output_dict or {}

    def _val(key: str, unit: str = "") -> str:
        v = od.get(key)
        if v in (None, ""):
            return ""
        return f"{v}{unit}"

    return Table(
        caption="Shear Connector Details",
        label="subsec:shear-connectors",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="p{10.0cm}"),
        ],
        rows=[
            ["Stud Diameter (mm)", _val("steeldesign.details.shear.diameter", " mm")],
            ["Stud Height (mm)", _val("steeldesign.details.shear.height", " mm")],
            [["Stud ", Math(r"f_y"), " (MPa)"], _val("steeldesign.details.shear.yield_strength", " MPa")],
            [["Stud ", Math(r"f_u"), " (MPa)"], _val("steeldesign.details.shear.ultimate_strength", " MPa")],
            ["No. of Studs per Section", _val("steeldesign.details.shear.studs_per_section")],
        ],
        layout=LayoutHints(space_after_mm=4),
        note="All values are per IRC 22 Table 1 unless user-modified.",
    )


# ---------------------------------------------------------------------------
# Semantic Partial Safety Factors table
# ---------------------------------------------------------------------------

def _build_safety_factors_table(facts: ReportFacts) -> Table:
    """Build a semantic Table for Partial Safety Factors from facts."""
    input_dict = facts.raw_input_dict or {}

    def _val(key: str) -> str:
        v = input_dict.get(key)
        return str(v) if v not in (None, "") else ""

    return Table(
        caption="Partial Safety Factors",
        label="subsec:safety-factors",
        columns=[
            Column("Parameter", width="L{5.5cm}"),
            Column("Value", width="p{10.0cm}"),
        ],
        rows=[
            [[Math(r"\gamma_{M0}"), r" (Yielding / Buckling)"], _val("design_options_cont.partial_factor.yielding_and_buckling.gamma_m0")],
            [[Math(r"\gamma_{M1}"), r" (Ultimate Stress)"], _val("design_options_cont.partial_factor.ultimate_stress.gamma_m1")],
            [[Math(r"\gamma_C"), r" (Concrete, Basic)"], _val("design_options_cont.partial_factor.concrete_basic.gamma_c_basic")],
            [[Math(r"\gamma_s"), r" (Reinforcement)"], _val("design_options_cont.partial_factor.reinforcing_steel.gamma_s")],
            [[Math(r"\gamma_v"), r" (Shear Connectors)"], _val("design_options_cont.partial_factor.shear_connectors.gamma_v")],
            [[Math(r"\gamma_{fft}"), r" (Fatigue Load)"], _val("design_options_cont.partial_factor.fatigue_load.gamma_flt")],
            [[Math(r"\gamma_{Mft}"), r" (Fatigue Strength)"], _val("design_options_cont.partial_factor.fatigue_strength.gamma_mf")],
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
