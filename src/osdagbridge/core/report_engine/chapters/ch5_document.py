"""Chapter 5: Design Checks — document builder (Phase 5A).

Builds semantic Table components from GirderDesignData for Tables 5.1–5.13.
"""

from __future__ import annotations

from ..document import Chapter, Column, RawLatex, Section, Table, TableGroup, Chart, Math, Callout, Paragraph
from ..layout import LayoutHints
from ..facts import (
    CheckStatus,
    DesignCheckData,
    GirderDesignData,
    QuantityValue,
    ReportFacts,
    ShearConnectorData,
    DeckDesignData,
    CrossBracingData,
    EndDiaphragmData,
    OverallSummaryData,
)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_qv(qv: QuantityValue | None, fallback: str = "---") -> str:
    """Format QuantityValue value as string without scientific notation."""
    if qv is None:
        return fallback
    v = qv.value
    if isinstance(v, (int, float)):
        if abs(v) >= 1e4:
            return f"{v:,.2f}".rstrip('0').rstrip('.')
        if abs(v) >= 1:
            return f"{v:.3f}".rstrip('0').rstrip('.')
        return f"{v:.4f}".rstrip('0').rstrip('.')
    return str(v)


def _fmt_status(status: CheckStatus) -> CheckStatus:
    """Return CheckStatus for LaTeX display, letting renderer handle colors."""
    if status is None:
        return CheckStatus.UNAVAILABLE
    return status


def _fmt_ratio(ur: float | None, nd: int = 2) -> str:
    """Format a ratio to nd decimal places."""
    if ur is None:
        return "---"
    return f"{ur:.{nd}f}"


def _fmt_qv_unit(qv: QuantityValue | None, fallback: str = "---") -> str:
    """Format QuantityValue with trailing unit."""
    if qv is None:
        return fallback
    v_str = _fmt_qv(qv, fallback)
    return f"{v_str} {qv.unit}" if qv.unit else v_str


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

COLS_3_PARAM = [Column("Girder", "C{1.5cm}"), Column("Parameter", "L{7.5cm}"), Column("Value", ">{\\centering\\arraybackslash}p{5.0cm}")]
COLS_5_CHECK = [Column("Girder", "C{1.5cm}"), Column("Parameter", "C{3.2cm}"), Column("Reference", "C{3.2cm}"), Column("Value", ">{\\centering\\arraybackslash}p{4.0cm}"), Column("Status", "C{1.8cm}")]
COLS_5_REQ   = [Column("Girder", "C{1.5cm}"), Column("Check", "L{3.2cm}"), Column("Required", "C{3.2cm}"), Column("Provided", ">{\\centering\\arraybackslash}p{4.0cm}"), Column("Status", "C{1.8cm}")]
COLS_5_DEF   = [Column("Girder", "C{1.5cm}"), Column("Check", "L{3.2cm}"), Column("Allowable", "C{3.2cm}"), Column("Actual", ">{\\centering\\arraybackslash}p{3.5cm}"), Column("Status", "C{2.0cm}")]


def _build_table_5_1(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.1 — Girder Section Properties."""
    groups = []
    for g in girders:
        sp = g.section_properties
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Depth, D (mm)", _fmt_qv(sp.depth)],
            [["Top Flange Width, ", Math(r"b_f"), " (mm)"], _fmt_qv(sp.top_flange_width)],
            [["Bottom Flange Width, ", Math(r"b_f"), " (mm)"], _fmt_qv(sp.bottom_flange_width)],
            [["Top Flange Thickness, ", Math(r"t_f"), " (mm)"], _fmt_qv(sp.top_flange_thickness)],
            [["Bottom Flange Thickness, ", Math(r"t_f"), " (mm)"], _fmt_qv(sp.bottom_flange_thickness)],
            [["Web Thickness, ", Math(r"t_w"), " (mm)"], _fmt_qv(sp.web_thickness)],
            [["Gross Area, ", Math(r"A"), " (", Math(r"cm^2"), ")"], _fmt_qv(sp.gross_area)],
            [["Moment of Inertia, ", Math(r"I_z"), " (", Math(r"cm^4"), ")"], _fmt_qv(sp.moment_of_inertia)],
            [["Elastic Section Modulus, ", Math(r"Z_{ez}"), " (", Math(r"cm^3"), ")"], _fmt_qv(sp.elastic_section_modulus)],
            [["Plastic Section Modulus, ", Math(r"Z_{pz}"), " (", Math(r"cm^3"), ")"], _fmt_qv(sp.plastic_section_modulus)],
            [["Effective Slab Width, ", Math(r"b_{eff}"), " (mm)"], _fmt_qv(sp.effective_slab_width)],
            [["Transformed Composite ", Math(r"I_z"), " (", Math(r"cm^4"), ")"], _fmt_qv(sp.composite_iz)],
            ["Depth to Plastic Neutral Axis (mm)", _fmt_qv(sp.pna_depth)],
        ]))
    return Table(
        caption="Girder Section Properties (Final Optimized / User-selected)",
        columns=COLS_3_PARAM,
        groups=groups,
    )


def _build_table_5_2(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.2 — Girder Section Classification."""
    cols = [
        Column("Girder", "C{1.5cm}"), Column("Element", "L{3.0cm}"),
        Column("Slenderness Ratio", "C{3.2cm}"),
        Column("Class Limit", "C{2.5cm}"),
        Column("Classification", ">{\\centering\\arraybackslash}p{3.5cm}"),
    ]
    groups = []
    for g in girders:
        c = g.classification
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Top Flange", _fmt_ratio(c.flange_slenderness), _fmt_ratio(c.flange_class_limit), c.class_flange or "---"],
            ["Web", _fmt_ratio(c.web_slenderness), _fmt_ratio(c.web_class_limit), c.class_web or "---"],
            ["Overall Section", "---", "---", c.section_class or "---"],
        ]))
    return Table(caption="Girder Section Classification", columns=cols, groups=groups, note="IS 800:2007 Table 2")


def _build_table_5_3(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.3 — Moment Capacity Check."""
    groups = []
    for g in girders:
        fl = g.flexure
        groups.append(TableGroup(label=g.girder_label, rows=[
            [["Applied Moment, ", Math(r"M_u")], "Governing LC (ULS)", _fmt_qv_unit(fl.mu_applied), "---"],
            [["Design Moment Capacity, ", Math(r"M_d")], "IRC 22 Cl. 603.3.1", _fmt_qv_unit(fl.md_capacity), "---"],
            [["Utilization Ratio, ", Math(r"M_u / M_d")], Math(r"M_u / M_d"), _fmt_ratio(fl.utilization_ratio), _fmt_status(fl.status)],
        ]))
    return Table(caption="Moment Capacity Check", columns=COLS_5_CHECK, groups=groups, note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1")


def _build_table_5_4(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.4 — Shear Capacity Check."""
    groups = []
    for g in girders:
        sh = g.shear
        groups.append(TableGroup(label=g.girder_label, rows=[
            [["Applied Shear, ", Math(r"V_u")], "Governing LC (ULS)", _fmt_qv_unit(sh.vu), "---"],
            [["Shear Area, ", Math(r"A_v")], Math(r"d_w \times t_w"), _fmt_qv_unit(sh.shear_av), "---"],
            ["Panel Aspect Ratio, c/d", "---", _fmt_ratio(sh.panel_cd), "---"],
            [["Shear Buckling Coeff, ", Math(r"k_v")], "IS 800 Cl. 8.4.2.2", _fmt_ratio(sh.shear_kv), "---"],
            [["Web Slenderness, ", Math(r"\lambda_w")], Math(r"\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}"), _fmt_ratio(sh.shear_lambda_w), "---"],
            [["Design Shear Stress, ", Math(r"\tau_b")], "IRC 22 Cl. 603.3.3.2", _fmt_qv_unit(sh.shear_tau_b), "---"],
            [["Shear Buckling Resistance, ", Math(r"V_{cr}")], Math(r"A_v \times \tau_b"), _fmt_qv_unit(sh.shear_vcr), "---"],
            [["Utilization Ratio, ", Math(r"V_u / V_d")], Math(r"V_u / V_d"), _fmt_ratio(sh.utilization_ratio), _fmt_status(sh.status)],
        ]))
    return Table(caption="Shear Capacity Check", columns=COLS_5_CHECK, groups=groups, note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2")


def _build_table_5_5(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.5 — Interaction Checks (M-V and M-N)."""
    cols = [
        Column("Girder", "C{1.5cm}"), Column("Check", "C{3.2cm}"),
        Column("Condition", "C{3.2cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.0cm}"),
        Column("Status", "C{1.8cm}"),
    ]
    groups = []
    for g in girders:
        ix = g.interaction
        if ix.mn_ratio is not None and ix.mn_axial is not None and ix.mn_moment is not None:
            mn_cond = f"{ix.mn_axial:.2f} + {ix.mn_moment:.2f} = {ix.mn_ratio:.3f}"
            mn_val = f"{ix.mn_ratio:.3f}"
        else:
            mn_cond = "N/A"
            mn_val = "N/A"
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["High Shear Condition?", Math(r"V_u > 0.6\,V_d"), ix.high_shear or "---", "---"],
            [["Reduced Moment Capacity, ", Math(r"M_{dv}")], "IRC 22 Cl. 603.3.3.3", _fmt_qv_unit(ix.mdv), "---"],
            [["Interaction Check: ", Math(r"M_u \leq M_{dv}")], "---", _fmt_ratio(ix.mv_ur), _fmt_status(ix.mv_status)],
            [["Interaction Check: ", Math(r"N_u/N_{Rd} + M_u/M_{dv} \leq 1.0")], mn_cond, mn_val, _fmt_status(ix.mn_status)],
        ]))
    return Table(caption="Interaction Checks (M-V and M-N)", columns=cols, groups=groups, note="IRC 22 Cl. 603.3.3.3")


def _build_table_5_6(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.6 — Lateral Torsional Buckling Check."""
    groups = []
    for g in girders:
        lt = g.ltb
        groups.append(TableGroup(label=g.girder_label, rows=[
            [["Elastic Critical Moment, ", Math(r"M_{cr}")], "IRC 22 Cl. 603.3.3.1", _fmt_qv_unit(lt.mcr), "---"],
            [["Non-dim. Slenderness, ", Math(r"\bar{\lambda}_{LT}")], Math(r"\sqrt{M_p / M_{cr}}"), _fmt_ratio(lt.ltb_lambda), "---"],
            [["LTB Reduction Factor, ", Math(r"\chi_{LT}")], "IS 800 Cl. 8.2.2", _fmt_ratio(lt.ltb_chi), "---"],
            [["LTB Resistance, ", Math(r"M_b")], Math(r"\chi_{LT}\,M_p / \gamma_{m0}"), _fmt_qv_unit(lt.ltb_mb), "---"],
            [[Math(r"M_u \leq M_b")], Math(r"M_u / M_b"), _fmt_ratio(lt.utilization_ratio), _fmt_status(lt.status)],
        ]))
    return Table(caption="Lateral Torsional Buckling Check -- Construction Stage", columns=COLS_5_CHECK, groups=groups, note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2")


def _build_table_5_7(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.7 — Stiffener Design Summary."""
    cols = [Column("Girder", "C{1.5cm}"), Column("Parameter", "L{6.5cm}"), Column("Value", ">{\\arraybackslash}p{6.0cm}")]
    groups = []
    for g in girders:
        st = g.stiffener_summary
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Shear Buckling Design Method", st.method or "---"],
            ["Intermediate Stiffener Thickness (mm)", _fmt_qv(st.int_thick)],
            ["Intermediate Stiffener Spacing (mm)", _fmt_qv(st.int_spacing)],
            ["End Panel Stiffener Thickness (mm)", _fmt_qv(st.end_thick)],
            ["No. of End Panel Stiffeners", str(st.end_count) if st.end_count is not None else "---"],
            ["Longitudinal Stiffeners", st.long_stiff or "---"],
        ]))
    return Table(caption="Stiffener Design Summary", columns=cols, groups=groups)


def _build_table_5_8(girders: tuple[GirderDesignData, ...]) -> Table | None:
    """Table 5.8 — Intermediate Stiffener Checks (Custom mode only)."""
    groups = []
    for g in girders:
        if g.intermediate_stiffener is None:
            continue
        ist = g.intermediate_stiffener
        groups.append(TableGroup(label=g.girder_label, rows=[
            [["Min. Moment of Inertia, ", Math(r"I_s")], _fmt_qv_unit(ist.iys_min), _fmt_qv_unit(ist.iys_prov), _fmt_status(ist.iys_status)],
            [["Buckling Resistance, ", Math(r"F_{qd} \geq F_q")], _fmt_qv_unit(ist.fq), _fmt_qv_unit(ist.fqd), _fmt_status(ist.fqd_status)],
        ]))
    if not groups:
        return None
    return Table(caption="Intermediate Stiffener Checks", columns=COLS_5_REQ, groups=groups, note="IS 800 Cl. 8.7.1.2")


def _build_table_5_9(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.9 — End Panel Stiffener Checks."""
    groups = []
    for g in girders:
        bs = g.bearing_stiffener
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Web Buckling Resistance", _fmt_qv_unit(bs.wb_req), _fmt_qv_unit(bs.wb_prov), _fmt_status(bs.wb_status)],
            ["Local Crushing Resistance", _fmt_qv_unit(bs.lc_req), _fmt_qv_unit(bs.lc_prov), _fmt_status(bs.lc_status)],
            ["Bearing Capacity", _fmt_qv_unit(bs.ps_req), _fmt_qv_unit(bs.ps_prov), _fmt_status(bs.ps_status)],
            ["Column Buckling Resistance", _fmt_qv_unit(bs.cb_req), _fmt_qv_unit(bs.cb_prov), _fmt_status(bs.cb_status)],
        ]))
    return Table(caption="End Panel Stiffener Checks", columns=COLS_5_REQ, groups=groups, note="IS 800 Cl. 8.4.2.2")


def _build_table_5_10(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.10 — Serviceability: Deflection Checks."""
    groups = []
    for g in girders:
        df = g.deflection
        allow_live = _fmt_qv_unit(df.allow_live) if df.allow_live else "---"
        allow_total = _fmt_qv_unit(df.allow_total) if df.allow_total else "---"
        groups.append(TableGroup(label=g.girder_label, rows=[
            [["Live Load Deflection, ", Math(r"\delta_{LL}"), " (mm)"], f"L/800 = {allow_live}", _fmt_qv(df.actual_live), _fmt_status(df.live_status)],
            [["Total Load Deflection, ", Math(r"\delta_{total}"), " (mm)"], f"L/600 = {allow_total}", _fmt_qv(df.actual_total), _fmt_status(df.total_status)],
        ]))
    return Table(caption="Serviceability -- Deflection Checks", columns=COLS_5_DEF, groups=groups, note="IRC 22 Cl. 604.3.2")


def _build_table_5_11(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.11 — Serviceability: Maximum Stress Limitation (flat, no groups)."""
    cols = [
        Column("Girder", "C{1.5cm}"), Column("Element", "L{3.5cm}"),
        Column("Allowable Stress", "C{3.2cm}"),
        Column("Actual Stress", ">{\\centering\\arraybackslash}p{3.5cm}"),
        Column("Status", "C{2.0cm}"),
    ]
    rows = []
    for g in girders:
        st = g.stress
        rows.append([
            g.girder_label,
            ["Structural Steel (", Math(r"0.9\,f_y"), ")"],
            _fmt_qv_unit(st.allowable_stress),
            _fmt_qv_unit(st.actual_stress),
            _fmt_status(st.status),
        ])
    return Table(caption="Serviceability -- Maximum Stress Limitation", columns=cols, rows=rows)


def _build_table_5_12(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.12 — Serviceability: Fatigue Assessment (flat, no groups)."""
    cols = [
        Column("Girder", "C{1.5cm}"), Column(["Stress Range, ", Math(r"\Delta\sigma"), " (MPa)"], "C{3.5cm}"),
        Column(["Fatigue Limit, ", Math(r"f_{fd}"), " (MPa)"], "C{3.5cm}"),
        Column("Utilization Ratio", ">{\\centering\\arraybackslash}p{3.2cm}"),
        Column("Status", "C{2.0cm}"),
    ]
    rows = []
    for g in girders:
        fa = g.fatigue
        rows.append([
            g.girder_label,
            _fmt_qv_unit(fa.stress_range),
            _fmt_qv_unit(fa.fatigue_limit),
            _fmt_ratio(fa.utilization_ratio),
            _fmt_status(fa.status),
        ])
    return Table(caption="Serviceability -- Fatigue Assessment", columns=cols, rows=rows, note=r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). Capacity reduction factor $\mu_r$ applied where plate thickness > 25 mm.")


def _build_table_5_13(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.13 — Girder Design Summary (flat, no groups)."""
    cols = [
        Column("Girder", "C{1.6cm}"),
        Column("Controlling LC / Combination", ">{\\centering\\arraybackslash}p{3.6cm}"),
        Column("Controlling Check", "C{2.4cm}"),
        Column("Demand", "C{2.0cm}"),
        Column("Capacity", "C{2.1cm}"),
        Column("UR", "C{1.7cm}"),
        Column("Status", "C{1.5cm}"),
    ]
    rows = []
    for g in girders:
        sm = g.summary
        rows.append([
            g.girder_label,
            sm.governing_lc or "",
            sm.controlling_check or "",
            _fmt_qv_unit(sm.demand) if sm.demand else "---",
            _fmt_qv_unit(sm.capacity) if sm.capacity else "---",
            _fmt_ratio(sm.dcr, nd=3),
            _fmt_status(sm.status),
        ])
    return Table(caption="Girder Design Summary (DCR / Utilization Ratio)", columns=cols, rows=rows, note=r"UR = Demand / Capacity. A value $\leq 1.0$ indicates a passing check. The controlling check is the criterion with the highest UR for each girder, with the real load case/combination that drives it.")


def _build_table_5_14(sc: ShearConnectorData) -> Table:
    """Table 5.14 — Shear Connector Capacity."""
    cols = [
        Column("Parameter", "L{5.0cm}"),
        Column("Formula", "L{6.0cm}"),
        Column("Value", "C{2.5cm}"),
        Column("Reference", "C{3.0cm}")
    ]
    rows = [
        [
            ["Design Resistance, ", Math(r"Q_u")],
            Math(r"\begin{gathered} Q_u=\min(Q_{u,s},\,Q_{u,c}) \\ Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v} \\ Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v} \end{gathered}"),
            _fmt_qv_unit(sc.design_resistance_qu),
            "IRC 22 Cl. 606.3.1 (Eq. 6.1)"
        ],
        [
            ["Fatigue Shear Resistance, ", Math(r"Q_r")],
            ["IRC 22 Table 8 (", Math(r"\phi d"), ", ", Math(r"N_{sc}"), ")"],
            _fmt_qv_unit(sc.fatigue_resistance_qr),
            "IRC 22 Cl. 606.3.2 (Table 8)"
        ]
    ]
    return Table(caption="Shear Connector Capacity (bridge-level)", columns=cols, rows=rows)


def _build_table_5_15(sc: ShearConnectorData) -> Table:
    """Table 5.15 — Shear Connector Spacing."""
    cols = [
        Column("Criterion", "L{3.2cm}"),
        Column("Governing Spacing", ">{\\centering\\arraybackslash}p{4.3cm}"),
        Column("Actual Spacing Provided", ">{\\centering\\arraybackslash}p{4.3cm}"),
        Column("Status", "C{2.0cm}")
    ]
    def _r(lbl, sp):
        return [lbl, _fmt_qv_unit(sp.required), _fmt_qv_unit(sp.provided), _fmt_status(sp.status)]
    
    rows = [
        _r("ULS Shear (SL1)", sc.uls_shear),
        _r("Full Composite (SL2)", sc.full_composite),
        _r("SLS Fatigue (SR)", sc.sls_fatigue),
        _r("Max Spacing Limit (IRC 22)", sc.max_limit),
    ]
    return Table(caption="Shear Connector Spacing", columns=cols, rows=rows, note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing = $\min(S_{L1}, S_{L2}, S_R)$.")


def _build_table_5_16(sc: ShearConnectorData) -> Table:
    """Table 5.16 — Transverse Shear & Detailing Checks."""
    cols = [
        Column("Check", "L{5.3cm}"),
        Column("Value", ">{\\arraybackslash}p{7.2cm}"),
        Column("Status", "C{2.0cm}")
    ]
    
    ts_ur_str = "---"
    if sc.transverse_ur is not None:
        ts_ur_str = f"{sc.transverse_ur:.2f}"
    
    ast_req_str = f"Required {_fmt_qv_unit(sc.min_transverse_reinf_req)}" if sc.min_transverse_reinf_req else "Required ---"
    ast_prov_str = f"Provided {_fmt_qv_unit(sc.min_transverse_reinf_prov)}" if sc.min_transverse_reinf_prov else "Provided ---"
    
    d_val = [Math(r"d"), f" = {_fmt_qv_unit(sc.stud_diameter)}"] if sc.stud_diameter else [Math(r"d"), " = ---"]
    d_lim = [Math(r"\leq 2t_f"), f" = {_fmt_qv_unit(sc.stud_diameter_limit)}"] if sc.stud_diameter_limit else [Math(r"\leq 2t_f"), " = ---"]
    
    edge_prov = f"Provided {_fmt_qv_unit(sc.edge_dist_prov)}" if sc.edge_dist_prov else "Provided ---"
    edge_req = ["(req. ", Math(r"\geq"), f" {_fmt_qv_unit(sc.edge_dist_req)})"] if sc.edge_dist_req else ["(req. ", Math(r"\geq"), " ---)"]

    rows = [
        [["Longitudinal Shear per unit length, ", Math(r"V_L")], _fmt_qv_unit(sc.vl_longitudinal), "---"],
        [["Transverse Shear Capacity of Slab, ", Math(r"V_{Rd}")], _fmt_qv_unit(sc.vrd_capacity), "---"],
        ["Transverse Shear Check", [Math(r"V_L/V_{Rd}"), " = ", ts_ur_str], _fmt_status(sc.transverse_status)],
        [["Min. Transverse Reinforcement, ", Math(r"A_{st,min}")], f"{ast_req_str}, {ast_prov_str}", _fmt_status(sc.reinf_status)],
        [["Stud Diameter ", Math(r"\leq 2\,t_f")], d_val + [" "] + d_lim, _fmt_status(sc.diameter_status)],
        ["Stud Edge Distance", [edge_prov, " "] + edge_req, _fmt_status(sc.edge_dist_status)],
    ]
    return Table(caption="Transverse Shear and Detailing Checks", columns=cols, rows=rows, note="IRC 22 Cl. 606.6, 606.10.")


def _build_table_5_17a(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{6.5cm}"), Column("Value", "p{9.0cm}")]
    ld = dk.loading
    
    cov_str = f"Top {_fmt_qv_unit(ld.clear_cover_top)} / Bottom {_fmt_qv_unit(ld.clear_cover_bot)}" if (ld.clear_cover_top and ld.clear_cover_bot) else "---"
    
    rows = [
        [["Effective Span of Deck Slab, ", Math(r"l_{eff}")], f"{_fmt_qv_unit(ld.effective_span)} (girder spacing, c/c)" if ld.effective_span else "---"],
        [["Deck Thickness, ", Math(r"t_s")], _fmt_qv_unit(ld.thickness)],
        ["Clear Cover (IRC 112 Cl. 15.2)", cov_str],
        ["Concrete Grade (IRC 112 Cl. 6.4)", [ld.concrete_grade or "---", " (", Math(r"f_{ck}"), f" = {_fmt_qv_unit(ld.fck)}, ", Math(r"f_{ctm}"), f" = {_fmt_qv_unit(ld.fctm)})"] if (ld.concrete_grade and ld.fck) else (ld.concrete_grade or "---")],
        ["Reinforcement Grade (IRC 112 Cl. 6.2)", [ld.reinf_grade or "---", " (", Math(r"f_y"), f" = {_fmt_qv_unit(ld.fy)})"] if (ld.reinf_grade and ld.fy) else (ld.reinf_grade or "---")],
        [["Dead Load per Unit Area, ", Math(r"w_{\mathrm{DL}}")], f"{_fmt_qv_unit(ld.dead_load)} (slab self-weight)" if ld.dead_load else "---"],
        ["IRC 6 Wheel Load (Class A / 70R)", _fmt_qv_unit(ld.wheel_load)],
        ["Tyre Contact Width (IRC 6 Annex A)", f"{_fmt_qv_unit(ld.tyre_width)} (transverse)" if ld.tyre_width else "---"],
        ["Impact Factor (IRC 6 Cl. 208.2)", f"{ld.impact_factor:.3f}" if ld.impact_factor is not None else "---"],
        ["Governing Live Load Case", ld.vehicle if ld.vehicle else "---"],
    ]
    return Table(caption="Deck Slab --- Loading and Geometry", columns=cols, rows=rows)


def _build_table_5_17b(dk: DeckDesignData) -> Table:
    cols = [
        Column("Location", "C{3.0cm}"),
        Column("Parameter", "C{3.5cm}"),
        Column("Formula / Reference", "C{3.2cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.2cm}"),
        Column("Status", "C{1.8cm}")
    ]
    fx = dk.flexure
    
    g_dl = f"{fx.gamma_dl:.2f}" if fx.gamma_dl is not None else "1.35"
    g_ll = f"{fx.gamma_ll:.2f}" if fx.gamma_ll is not None else "1.50"
    
    rows = [
        ["At Midspan (Sagging)", ["Transverse BM (DL), ", Math(r"M_{T,DL}")], Math(r"w_{\mathrm{DL}}\,l_{eff}^2/10"), _fmt_qv_unit(fx.m_dl_sag), "---"],
        ["At Midspan (Sagging)", ["Transverse BM (LL), ", Math(r"M_{T,LL}")], "Effective width (IRC 112 B3.1)", _fmt_qv_unit(fx.m_ll_sag), "---"],
        ["At Midspan (Sagging)", ["Total Design BM, ", Math(r"M_{u,sag}")], f"{g_dl} DL + {g_ll} LL", _fmt_qv_unit(fx.demand_sagging), "---"],
        ["At Midspan (Sagging)", ["Effective depth, ", Math(r"d")], Math(r"t_s - c_{nom} - \phi/2"), _fmt_qv_unit(fx.d_bot), "---"],
        ["At Midspan (Sagging)", ["Moment Capacity, ", Math(r"M_{Rd}")], "IRC 112 Cl. 12.2", _fmt_qv_unit(fx.capacity_sagging), _fmt_status(fx.status_sagging)],
        
        ["At Support (Hogging)", ["Total Design BM, ", Math(r"M_{u,hog}")], f"{g_dl} DL + {g_ll} LL (at support)", _fmt_qv_unit(fx.demand_hogging), "---"],
        ["At Support (Hogging)", ["Required Top Steel, ", Math(r"A_{st,top}")], Math(r"M_u / (0.87\,f_y\,d)"), _fmt_qv_unit(fx.required_top_steel), "---"],
        ["At Support (Hogging)", ["Moment Capacity, ", Math(r"M_{Rd}")], "IRC 112 Cl. 12.2", _fmt_qv_unit(fx.capacity_hogging), _fmt_status(fx.status_hogging)],
    ]
    return Table(
        caption="Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)",
        columns=cols,
        rows=rows,
        note="IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20% of main steel moment (IRC 21 Cl. 305.18)."
    )


def _build_table_5_17c(dk: DeckDesignData) -> Table:
    cols = [
        Column("Parameter", "L{5.5cm}"),
        Column("Formula", "C{3.5cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.5cm}"),
        Column("Status", "C{2cm}")
    ]
    fx = dk.flexure
    if not fx.has_overhang:
        rows = [["No Overhang", "---", "N/A", "---"]]
    else:
        g_dl = f"{fx.gamma_dl:.2f}" if fx.gamma_dl is not None else "1.35"
        g_ll = f"{fx.gamma_ll:.2f}" if fx.gamma_ll is not None else "1.50"
        rows = [
            [["Overhang Length, ", Math(r"l_{oh}")], "---", _fmt_qv_unit(fx.overhang_length), "---"],
            ["Crash Barrier Load Moment", "IRC 6 Cl. 206.4", _fmt_qv_unit(fx.m_barrier), "---"],
            ["Dead Load Moment", [Math(r"w_{\mathrm{DL}}\,l_{oh}^2/2"), " + railing"], _fmt_qv_unit(fx.m_dl_oh), "---"],
            ["Live Load Moment (eccentric wheel)", [Math(r"\text{Wheel load} \times \text{arm}")], _fmt_qv_unit(fx.m_ll_oh), "---"],
            [["Total Hogging Moment, ", Math(r"M_{u,oh}")], f"{g_dl} DL + {g_ll} (LL + CB)", _fmt_qv_unit(fx.demand_overhang), "---"],
            [["Moment Capacity (top steel), ", Math(r"M_{Rd,oh}")], "IRC 112 Cl. 12.2", _fmt_qv_unit(fx.capacity_overhang), _fmt_status(fx.status_overhang)],
        ]
    return Table(
        caption="Deck Slab --- Cantilever Overhang Flexure Check",
        columns=cols,
        rows=rows,
        note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure."
    )


def _build_table_5_17d(dk: DeckDesignData) -> Table:
    cols = [
        Column("Parameter", "L{5.5cm}"),
        Column("Formula / Reference", "C{3.5cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.5cm}"),
        Column("Status", "C{2cm}")
    ]
    sh = dk.shear
    
    ur_str = "---"
    if sh.punching_ur is not None:
        ur_str = f"{sh.punching_ur:.2f}"
    
    tyre_str = f"{_fmt_qv(sh.tyre_width)} × {_fmt_qv(sh.tyre_length)} mm" if (sh.tyre_width and sh.tyre_length) else "---"
    c1_c2_str = f"{_fmt_qv(sh.punching_c1)} × {_fmt_qv(sh.punching_c2)} mm" if (sh.punching_c1 and sh.punching_c2) else "---"
    
    rows = [
        [["Design Wheel Load (ULS), ", Math(r"V_{Ed}")], Math(r"\gamma_Q\,(1+IF)\,P_w"), _fmt_qv_unit(sh.punching_ved_kn), "---"],
        ["Tyre Contact Area", [Math(r"a \times b"), " (IRC 6 Annex A)"], tyre_str, "---"],
        [["Loaded Area at mid-depth, ", Math(r"b_0")], [Math(r"c_1 \times c_2"), " (incl. WC dispersion)"], c1_c2_str, "---"],
        [["Control Perimeter, ", Math(r"u_1")], Math(r"2(c_1+c_2) + 4\pi d"), _fmt_qv_unit(sh.punching_u1), "---"],
        [["Punching Shear Stress, ", Math(r"v_{Ed}")], Math(r"V_{Ed} / (u_1\,d)"), _fmt_qv_unit(sh.punching_ved_mpa), "---"],
        [["Punching Resistance, ", Math(r"v_{Rd,c}")], "IRC 112 Eq. 10.1", _fmt_qv_unit(sh.punching_vrdc_mpa), "---"],
        ["Punching Shear Check", Math(r"v_{Ed} \leq v_{Rd,c}"), ur_str, _fmt_status(sh.punching_status)],
    ]
    return Table(
        caption="Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)",
        columns=cols,
        rows=rows,
        note="Punching shear reinforcement not typically required for deck slabs with d ≥ 200 mm and adequate longitudinal reinforcement."
    )


def _build_table_5_17e(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{7cm}"), Column("Value / Reference", ">{\\arraybackslash}p{8.5cm}")]
    cw = dk.crack_width
    
    min_str = f"{_fmt_qv_unit(cw.as_min)} [IRC 112 Cl. 16.5.1]" if cw.as_min else "---"
    prov_str = [Math(r"\phi"), f"{_fmt_qv(cw.dia_bot)} @ {_fmt_qv(cw.spc_bot)} mm c/c ({_fmt_qv_unit(cw.as_bot)})"] if (cw.dia_bot and cw.spc_bot and cw.as_bot) else "---"
    
    rows = [
        [["Min. Reinforcement for Crack Control, ", Math(r"A_{s,min}")], min_str],
        ["Provided Reinforcement (bottom)", prov_str],
        ["Max. Permissible Crack Width", _fmt_qv_unit(cw.limit)],
        [["Calculated Crack Width, ", Math(r"w_k"), " (governing)"], _fmt_qv_unit(cw.calculated)],
        ["Crack Width Check", _fmt_status(cw.status)],
    ]
    return Table(caption="Crack Width Check (Deck Slab)", columns=cols, rows=rows)


def _build_table_5_17f(dk: DeckDesignData) -> Table:
    cols = [
        Column("Parameter", "L{5.5cm}"),
        Column("Formula / Reference", "C{3.5cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.5cm}"),
        Column("Status", "C{2cm}")
    ]
    sh = dk.shear
    
    ur_str = "---"
    if sh.oneway_ur is not None:
        ur_str = f"{sh.oneway_ur:.2f}"
        
    k_str = f"{sh.oneway_size_factor_k:.3f}" if sh.oneway_size_factor_k is not None else "---"
    rho_str = f"{sh.oneway_rho_l:.4f}" if sh.oneway_rho_l is not None else "---"
        
    rows = [
        [["Design Shear per unit width, ", Math(r"V_{Ed}")], Math(r"\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}"), _fmt_qv_unit(sh.oneway_ved), "---"],
        [["Effective depth, ", Math(r"d")], Math(r"t_s - c_{nom} - \phi/2"), _fmt_qv_unit(sh.d_bot), "---"],
        [["Size factor, ", Math(r"k")], Math(r"1 + \sqrt{200/d} \leq 2.0"), k_str, "---"],
        [["Longitudinal reinforcement ratio, ", Math(r"\rho_l")], Math(r"A_{sl}/(b_w\,d) \leq 0.02"), rho_str, "---"],
        [["Shear resistance (no stirrups), ", Math(r"V_{Rd,c}")], [Math(r"v_{Rd,c}\,b_w\,d"), " (Cl. 10.3.2)"], _fmt_qv_unit(sh.oneway_vrdc), "---"],
        ["One-Way Shear Check", Math(r"V_{Ed} \leq V_{Rd,c}"), ur_str, _fmt_status(sh.oneway_status)],
    ]
    return Table(
        caption="One-Way (Beam) Shear Check (Deck Slab)",
        columns=cols,
        rows=rows,
        note="IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement."
    )


def _build_table_5_17g(dk: DeckDesignData) -> Table:
    cols = [
        Column("Parameter", "L{5.5cm}"),
        Column("Required / Limit", ">{\\centering\\arraybackslash}p{4.1cm}"),
        Column("Provided", ">{\\centering\\arraybackslash}p{4.1cm}"),
        Column("Status", "C{1.8cm}")
    ]
    dt = dk.detailing
    
    dia_spc_str = [Math(r"\phi"), f"{_fmt_qv(dt.dia_bot)} @ {_fmt_qv(dt.spc_bot)} mm c/c"] if (dt.dia_bot and dt.spc_bot) else "---"
    cov_str = f"Top {_fmt_qv_unit(dt.top_cover)} / Bottom {_fmt_qv_unit(dt.bot_cover)}" if (dt.top_cover and dt.bot_cover) else "---"
    
    rows = [
        # Group 1: Main Reinforcement — Bottom (Transverse)
        ["Main Reinforcement — Bottom (Transverse)", "", "", ""],
        [["Required Area, ", Math(r"A_{st,req}"), " (mm²/m)"], _fmt_qv_unit(dt.required_bottom), _fmt_qv_unit(dt.provided_bottom), _fmt_status(dt.status_bottom)],
        ["Bar Diameter × Spacing", [Math(r"\phi \geq 10"), " mm (IRC 112)"], dia_spc_str, "---"],
        [["Min. Reinforcement ", Math(r"A_{s,min}"), " (IRC 112 Cl. 16.3.1)"], _fmt_qv_unit(dt.as_min), _fmt_qv_unit(dt.provided_bottom), _fmt_status(dt.status_bottom)],
        ["Max. Bar Spacing (IRC 112 Cl. 16.3.2)", _fmt_qv_unit(dt.spc_max), f"{_fmt_qv(dt.spc_bot)} mm" if dt.spc_bot else "---", _fmt_status(CheckStatus.PASS if (dt.spc_bot and dt.spc_max and dt.spc_bot.value <= dt.spc_max.value) else CheckStatus.FAIL)],
        
        # Group 2: Distribution Reinforcement — Longitudinal
        ["Distribution Reinforcement — Longitudinal", "", "", ""],
        [["Required Area, ", Math(r"A_{st,dist}"), " (mm²/m)"], [Math(r"\geq 20\%"), " of main steel"], _fmt_qv_unit(dt.provided_dist), _fmt_status(dt.status_dist)],
        
        # Group 3: Top Reinforcement (Support / Cantilever Overhang)
        ["Top Reinforcement (Support / Cantilever Overhang)", "", "", ""],
        [["Required Area, ", Math(r"A_{st,top}"), " (mm²/m)"], _fmt_qv_unit(dt.required_top), _fmt_qv_unit(dt.provided_top), _fmt_status(dt.status_top)],
        
        # Group 4: Cover and Detailing
        ["Cover and Detailing", "", "", ""],
        ["Clear Cover (IRC 112 Cl. 15.2)", [Math(r"\geq "), _fmt_qv_unit(dt.min_cover), " (Table 14.2)"] if dt.min_cover else "---", cov_str, _fmt_status(dt.status_cover)],
    ]
    return Table(
        caption="Reinforcement Detailing Summary (Deck Slab)",
        columns=cols,
        rows=rows,
        note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5. All reinforcement provisions satisfy strength and detailing requirements."
    )


# ---------------------------------------------------------------------------
# Phase 5C: Cross Bracing, End Diaphragm, and Overall Summary
# ---------------------------------------------------------------------------

def _build_table_5_20a(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Connection", "C{2.5cm}"), Column("Section", "C{3.0cm}"),
        Column([Math(r"A_g"), " (mm", Math(r"^2"), ")"], "C{2.5cm}"), Column([Math(r"r_{min}"), " (mm)"], "C{2.5cm}")
    ]
    if not cb or not cb.panels:
        return Table(caption="Cross Bracing --- Connection and Section Properties", columns=cols, rows=[["---"] * 6])
    
    rows = []
    for p in cb.panels:
        for m_name, m_label in [("diagonal", "Diagonal"), ("chord", "Chord")]:
            mem = p.diagonal_tension if m_name == "diagonal" else p.chord_tension
            if not mem: mem = p.diagonal_compression if m_name == "diagonal" else p.chord_compression
            if not mem: continue
            
            rows.append([
                p.pair_label, m_label, mem.connection_type or "---", mem.section or "---",
                _fmt_qv(mem.gross_area), _fmt_qv(mem.rmin)
            ])
            
    if not rows:
        rows = [["---"] * 6]

    return Table(caption="Cross Bracing --- Connection and Section Properties", columns=cols, rows=rows, note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.")


def _build_table_5_20b(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Nature", "C{2.0cm}"),
        Column(["Eff. Length ", Math(r"KL"), " (mm)"], "C{3.5cm}"), Column(Math(r"KL/r"), "C{2.5cm}"),
        Column("Limit", "C{2.0cm}"), Column("Status", "C{2.0cm}")
    ]
    if not cb or not cb.panels:
        return Table(caption="Cross Bracing --- Slenderness Ratio Check", columns=cols, rows=[["---"] * 7])
    
    rows = []
    for p in cb.panels:
        members_to_check = [
            ("Diagonal", "C", p.diagonal_compression or p.diagonal_tension),
            ("Top chord", "C", p.chord_compression),
            ("Bottom chord", "T", p.chord_tension),
        ]
        for m_label, nature, mem in members_to_check:
            if mem is None:
                continue
            kl_str = _fmt_qv(mem.effective_length)
            slnd_str = f"{mem.slenderness:.1f}" if mem.slenderness is not None else "---"
            lim_str = f"{mem.slenderness_limit:.0f}" if mem.slenderness_limit is not None else "---"
            
            if mem.slenderness is not None and mem.slenderness_limit is not None:
                status = CheckStatus.PASS if mem.slenderness <= mem.slenderness_limit else CheckStatus.FAIL
            else:
                status = CheckStatus.UNAVAILABLE
                
            rows.append([
                p.pair_label, m_label, nature, kl_str, slnd_str, lim_str, _fmt_status(status)
            ])
            
    if not rows:
        rows = [["---"] * 7]
        
    return Table(caption="Cross Bracing --- Slenderness Ratio Check", columns=cols, rows=rows, layout=LayoutHints(splittable=True), note="Limit = 250 for compression members, 400 for tension members. K = 1.0 for members with both ends pinned.")


def _build_table_5_20c(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Section", "C{2.5cm}"),
        Column("Governing LC", "C{3.5cm}"), Column("Demand (kN)", "C{2.5cm}"), Column("Capacity (kN)", "C{2.5cm}"),
        Column("UR", "C{1.8cm}"), Column("Status", "C{1.8cm}")
    ]
    if not cb or not cb.panels:
        return Table(caption="Cross Bracing Design --- Capacity Summary", columns=cols, rows=[["---"] * 8], layout=LayoutHints(splittable=True))
        
    rows = []
    for p in cb.panels:
        for force_type in ["tension", "compression"]:
            best = None
            m_label = ""
            for m_name, m_attr in [("Diagonal", p.diagonal_tension if force_type == "tension" else p.diagonal_compression),
                                   ("Chord", p.chord_tension if force_type == "tension" else p.chord_compression)]:
                if m_attr and m_attr.ur is not None:
                    if best is None or m_attr.ur > best.ur:
                        best = m_attr
                        m_label = m_name
            if best:
                rows.append([
                    p.pair_label, f"{m_label} ({force_type.title()})", best.section or "---",
                    best.governing_lc or "---", _fmt_qv(best.demand), _fmt_qv(best.capacity),
                    _fmt_ratio(best.ur), _fmt_status(best.status)
                ])
                
    if not rows:
        rows = [["---"] * 8]
        
    return Table(caption="Cross Bracing Design --- Capacity Summary", columns=cols, rows=rows, layout=LayoutHints(minimum_bottom_clearance_lines=10), note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.")


def _build_table_5_27(ed: EndDiaphragmData | None) -> Table:
    """Build End Diaphragm --- Connection and Section Properties."""
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Connection", "C{2.5cm}"), Column("Section", "C{3.0cm}"),
        Column([Math(r"A_g"), " (mm", Math(r"^2"), ")"], "C{2.5cm}"), Column([Math(r"r_{min}"), " (mm)"], "C{2.5cm}")
    ]
    if not ed or not ed.panels:
        return Table(caption="End Diaphragm --- Connection and Section Properties", columns=cols, rows=[["---"] * 6], note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.")

    rows = []
    for p in ed.panels:
        for m_name, m_label in [("diagonal", "Diagonal"), ("chord", "Chord")]:
            mem = p.diagonal_tension if m_name == "diagonal" else p.chord_tension
            if not mem:
                mem = p.diagonal_compression if m_name == "diagonal" else p.chord_compression
            if not mem:
                continue

            rows.append([
                p.pair_label, m_label, mem.connection_type or "---", mem.section or "---",
                _fmt_qv(mem.gross_area), _fmt_qv(mem.rmin)
            ])

    if not rows:
        rows = [["---"] * 6]

    return Table(
        caption="End Diaphragm --- Connection and Section Properties",
        columns=cols,
        rows=rows,
        note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.",
    )


def _build_table_5_28(ed: EndDiaphragmData | None) -> Table:
    """Build End Diaphragm --- Slenderness Ratio Check."""
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Nature", "C{2.0cm}"),
        Column(["Eff. Length ", Math(r"KL"), " (mm)"], "C{3.5cm}"), Column(Math(r"KL/r"), "C{2.5cm}"),
        Column("Limit", "C{2.0cm}"), Column("Status", "C{2.0cm}")
    ]
    if not ed or not ed.panels:
        return Table(caption="End Diaphragm --- Slenderness Ratio Check (IS 800 Cl. 3.8)", columns=cols, rows=[["---"] * 7], note="Limit = 250 for compression members, 400 for tension members. K = 1.0 for members with both ends pinned.")

    rows = []
    for p in ed.panels:
        members_to_check = [
            ("Diagonal", "C", p.diagonal_compression or p.diagonal_tension),
            ("Top chord", "C", p.chord_compression),
            ("Bottom chord", "T", p.chord_tension),
        ]
        for m_label, nature, mem in members_to_check:
            if mem is None:
                continue
            kl_str = _fmt_qv(mem.effective_length)
            slnd_str = f"{mem.slenderness:.1f}" if mem.slenderness is not None else "---"
            lim_str = f"{mem.slenderness_limit:.0f}" if mem.slenderness_limit is not None else "---"

            if mem.slenderness is not None and mem.slenderness_limit is not None:
                status = CheckStatus.PASS if mem.slenderness <= mem.slenderness_limit else CheckStatus.FAIL
            else:
                status = CheckStatus.UNAVAILABLE

            rows.append([
                p.pair_label, m_label, nature, kl_str, slnd_str, lim_str, _fmt_status(status)
            ])

    if not rows:
        rows = [["---"] * 7]

    return Table(
        caption="End Diaphragm --- Slenderness Ratio Check (IS 800 Cl. 3.8)",
        columns=cols,
        rows=rows,
        layout=LayoutHints(splittable=True),
        note="Limit = 250 for compression members, 400 for tension members. K = 1.0 for members with both ends pinned.",
    )


def _build_table_5_29(ed: EndDiaphragmData | None) -> Table:
    """Build End Diaphragm Design --- Capacity Summary."""
    cols = [
        Column("Panel", "C{2.0cm}"), Column("Member", "C{2.5cm}"), Column("Section", "C{2.5cm}"),
        Column("Governing LC", "C{3.5cm}"), Column("Demand (kN)", "C{2.5cm}"), Column("Capacity (kN)", "C{2.5cm}"),
        Column("UR", "C{1.8cm}"), Column("Status", "C{1.8cm}")
    ]
    if not ed or not ed.panels:
        return Table(caption="End Diaphragm Design --- Capacity Summary", columns=cols, rows=[["---"] * 8], layout=LayoutHints(minimum_bottom_clearance_lines=10), note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.")

    rows = []
    for p in ed.panels:
        for force_type in ["tension", "compression"]:
            best = None
            m_label = ""
            for m_name, m_attr in [("Diagonal", p.diagonal_tension if force_type == "tension" else p.diagonal_compression),
                                   ("Chord", p.chord_tension if force_type == "tension" else p.chord_compression)]:
                if m_attr and m_attr.ur is not None:
                    if best is None or m_attr.ur > best.ur:
                        best = m_attr
                        m_label = m_name
            if best:
                rows.append([
                    p.pair_label, f"{m_label} ({force_type.title()})", best.section or "---",
                    best.governing_lc or "---", _fmt_qv(best.demand), _fmt_qv(best.capacity),
                    _fmt_ratio(best.ur), _fmt_status(best.status)
                ])

    if not rows:
        rows = [["---"] * 8]

    return Table(caption="End Diaphragm Design --- Capacity Summary", columns=cols, rows=rows, note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension). OsdagBridge cross-bracing module used.")


def _build_table_5_30(summary: OverallSummaryData | None) -> Table:
    """Build Overall Design Check Summary table."""
    cols = [
        Column("Check / Member", "L{5.0cm}"), Column("Governing LC", "L{5.0cm}"),
        Column("Demand", "C{2.5cm}"), Column("Capacity", "C{2.5cm}"), Column("UR", "C{2.0cm}"), Column("Status", "C{2.0cm}")
    ]
    if not summary:
        return Table(caption="Overall Design Check Summary", columns=cols, rows=[["---"] * 6])

    rows = []
    for comp in (summary.girders, summary.deck, summary.cross_bracing, summary.end_diaphragm):
        if not comp: continue
        for r in comp.records:
            if r.demand is None and r.capacity is None and r.ur is None and r.status in (None, CheckStatus.UNAVAILABLE):
                continue
            rows.append([
                r.label,
                r.governing_lc or "---",
                _fmt_qv_unit(r.demand),
                _fmt_qv_unit(r.capacity),
                _fmt_ratio(r.ur),
                _fmt_status(r.status)
            ])

    return Table(
        caption="Overall Design Check Summary",
        columns=cols,
        rows=rows,
        label="tab:ch5_overall_summary",
        note=r"UR = Demand / Capacity. All values $\leq 1.0$ indicate passing checks. The governing check for each component is highlighted in the individual design check sections above.",
    )


def build_chapter_5(facts: ReportFacts) -> Chapter:
    """Build Chapter 5: Design Checks.

    Builds semantic Table components from typed DesignCheckData organized
    into logical Sections (with landscape layouts for wide member designs).
    """
    sections: list[Section] = []

    if facts.design_check_data is not None:
        gd = facts.design_check_data

        # Chapter 5 introductory text directly under \chapter{Design Checks}
        sections.append(
            Section(
                title="",
                level=2,
                components=[
                    Paragraph(
                        "This section presents all structural design checks performed by OsdagBridge. For each "
                        "member, the demand from the governing load combination, the code-based capacity, and "
                        "the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 "
                        "unless stated otherwise."
                    )
                ]
            )
        )

        # --- Section 5.1: Plate Girder Design ---
        girder_comps: list[DocumentComponent] = []
        if gd.girders:
            tables = [
                _build_table_5_1(gd.girders),
                _build_table_5_2(gd.girders),
                _build_table_5_3(gd.girders),
                _build_table_5_4(gd.girders),
                _build_table_5_5(gd.girders),
                _build_table_5_6(gd.girders),
                _build_table_5_7(gd.girders),
                _build_table_5_8(gd.girders),
                _build_table_5_9(gd.girders),
                _build_table_5_10(gd.girders),
                _build_table_5_11(gd.girders),
                _build_table_5_12(gd.girders),
                _build_table_5_13(gd.girders),
            ]
            for tbl in tables:
                if tbl is not None:
                    girder_comps.append(tbl)

        if gd.shear_connectors:
            sc = gd.shear_connectors
            girder_comps.append(_build_table_5_14(sc))
            girder_comps.append(_build_table_5_15(sc))
            girder_comps.append(_build_table_5_16(sc))

        if girder_comps:
            sections.append(Section(title="Plate Girder Design", level=2, components=girder_comps))

        # --- Section 5.2: Deck Slab Design ---
        if gd.deck and gd.deck.is_designed:
            dk = gd.deck
            deck_comps: list[DocumentComponent] = [
                Paragraph("The reinforced concrete deck slab is designed per IRC 112:2011 (flexure, shear, crack width) and IRC 22:2014 (composite construction). Wheel loads are distributed using Pigeaud’s method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing."),
                _build_table_5_17a(dk),
                _build_table_5_17b(dk),
                _build_table_5_17c(dk),
                _build_table_5_17d(dk),
                _build_table_5_17e(dk),
                _build_table_5_17f(dk),
                _build_table_5_17g(dk),
            ]
            sections.append(Section(title="Deck Slab Design", level=2, components=deck_comps))

        # --- Section 5.3: Cross Bracing Design (Landscape) ---
        cb = gd.cross_bracing
        if cb and cb.panels:
            cb_comps: list[DocumentComponent] = [
                Paragraph("Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS 800:2007 Cl. 7 (compression) and Cl. 6 (tension). Forces are derived from the grillage model under the governing load combination (DL + LL + WL)."),
                _build_table_5_20a(cb),
                _build_table_5_20b(cb),
                _build_table_5_20c(cb),
            ]
            sections.append(Section(title="Cross Bracing Design", level=2, components=cb_comps, layout=LayoutHints(orientation="landscape")))

        # --- Section 5.4: End Diaphragm Design (Landscape) ---
        ed = gd.end_diaphragm
        if ed:
            ed_comps: list[DocumentComponent] = [
                Paragraph("End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS 800:2007 and IRC 24:2010 Cl. 507."),
                _build_table_5_27(ed),
                _build_table_5_28(ed),
                _build_table_5_29(ed),
            ]
            sections.append(Section(title="End Diaphragm Design", level=2, components=ed_comps, layout=LayoutHints(orientation="landscape")))

        # --- Section 5.5: Overall Design Check Summary (Landscape) ---
        summary = gd.summary
        if summary:
            summary_comps: list[DocumentComponent] = [
                _build_table_5_30(summary),
            ]
            if summary.end_diaphragm and summary.end_diaphragm.status == CheckStatus.UNAVAILABLE:
                summary_comps.append(Callout("End Diaphragm rolled/welded section design to be added.", callout_type="note"))

            summary_comps.append(
                Paragraph("The chart below illustrates the governing utilization ratios for all primary superstructure components. Ratios exceeding 1.0 indicate demand exceeding capacity under the governing limit state load combinations.")
            )

            ur_chart = Chart(
                title="Overall Utilization Ratio by Component",
                chart_type="barh",
                data={
                    "Steel Plate Girders": summary.girders.max_ur,
                    "Concrete Deck Slab": summary.deck.max_ur,
                    "Cross Bracing": summary.cross_bracing.max_ur if summary.cross_bracing else None,
                    "End Diaphragms": summary.end_diaphragm.max_ur if summary.end_diaphragm else None,
                },
                x_label="Utilization Ratio (Demand / Capacity)",
                threshold_line=1.0,
                width_cm=19.5,
                height_cm=8.5,
            )
            summary_comps.append(ur_chart)
            sections.append(Section(title="Overall Design Check Summary", level=2, components=summary_comps, layout=LayoutHints(orientation="landscape")))
    else:
        # Fallback: delegate to legacy ch5_design_checks
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.reports.report_generator import ReportDataBridge

        input_dict = facts.raw_input_dict or {}
        output_dict = facts.raw_output_dict or {}

        bridge = ReportDataBridge(output_dict, input_dict, _PayloadProxy(facts))
        latex = ch5_design_checks(facts.design_checks or [], bridge)
        sections.append(Section(title="", level=2, components=[RawLatex(latex)]))

    return Chapter(
        number=5,
        title="Design Checks",
        sections=sections,
    )


class _PayloadProxy:
    """Minimal proxy satisfying the ReportPayload interface accessed by
    ReportDataBridge -- only ``design_checks`` is read."""

    def __init__(self, facts: ReportFacts):
        self.design_checks = facts.design_checks or []
