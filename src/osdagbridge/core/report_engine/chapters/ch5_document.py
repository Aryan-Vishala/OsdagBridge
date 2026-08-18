"""Chapter 5: Design Checks — document builder (Phase 5A).

Builds semantic Table components from GirderDesignData for Tables 5.1–5.13.
"""

from __future__ import annotations

from ..document import Chapter, Column, RawLatex, Section, Table, TableGroup
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
    """Format a QuantityValue for table display."""
    if qv is None:
        return fallback
    return f"{qv.value:g}"


def _fmt_status(status: CheckStatus) -> str:
    """Format CheckStatus for LaTeX display."""
    _map = {
        CheckStatus.PASS: "PASS",
        CheckStatus.WARN: "WARN",
        CheckStatus.FAIL: r"\textcolor{red}{FAIL}",
        CheckStatus.UNAVAILABLE: "---",
    }
    return _map.get(status, "---")


def _fmt_ratio(ur: float | None, nd: int = 2) -> str:
    """Format a ratio to nd decimal places."""
    if ur is None:
        return "---"
    return f"{ur:.{nd}f}"


def _fmt_qv_unit(qv: QuantityValue | None, fallback: str = "---") -> str:
    """Format QuantityValue with trailing unit."""
    if qv is None:
        return fallback
    return f"{qv.value:g} {qv.unit}" if qv.unit else f"{qv.value:g}"


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

COLS_3_PARAM = [Column(""), Column("Parameter", "L{8.0cm}"), Column("Value", ">{\\centering\\arraybackslash}p{5.0cm}")]
COLS_5_CHECK = [Column(""), Column("Parameter", "C{3.5cm}"), Column("Reference", "C{3.5cm}"), Column("Value", ">{\\centering\\arraybackslash}p{4.2cm}"), Column("Status", "C{1.8cm}")]
COLS_5_REQ   = [Column(""), Column("Check", "L{3.5cm}"), Column("Required", "C{3.5cm}"), Column("Provided", ">{\\centering\\arraybackslash}p{4.2cm}"), Column("Status", "C{1.8cm}")]
COLS_5_DEF   = [Column(""), Column("Check", "L{3.5cm}"), Column("Allowable", "C{3.5cm}"), Column("Actual", ">{\\centering\\arraybackslash}p{3.5cm}"), Column("Status", "C{2.5cm}")]


def _build_table_5_1(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.1 — Girder Section Properties."""
    groups = []
    for g in girders:
        sp = g.section_properties
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Depth, D (mm)", _fmt_qv(sp.depth)],
            ["Top Flange Width, b\\textsubscript{f} (mm)", _fmt_qv(sp.top_flange_width)],
            ["Bottom Flange Width, b\\textsubscript{f} (mm)", _fmt_qv(sp.bottom_flange_width)],
            ["Top Flange Thickness, t\\textsubscript{f} (mm)", _fmt_qv(sp.top_flange_thickness)],
            ["Bottom Flange Thickness, t\\textsubscript{f} (mm)", _fmt_qv(sp.bottom_flange_thickness)],
            ["Web Thickness, t\\textsubscript{w} (mm)", _fmt_qv(sp.web_thickness)],
            ["Gross Area, A (cm\\textsuperscript{2})", _fmt_qv(sp.gross_area)],
            ["Moment of Inertia, I\\textsubscript{z} (cm\\textsuperscript{4})", _fmt_qv(sp.moment_of_inertia)],
            ["Elastic Section Modulus, Z\\textsubscript{ez} (cm\\textsuperscript{3})", _fmt_qv(sp.elastic_section_modulus)],
            ["Plastic Section Modulus, Z\\textsubscript{pz} (cm\\textsuperscript{3})", _fmt_qv(sp.plastic_section_modulus)],
            ["Effective Slab Width, b\\textsubscript{eff} (mm)", _fmt_qv(sp.effective_slab_width)],
            ["Transformed Composite I\\textsubscript{z} (cm\\textsuperscript{4})", _fmt_qv(sp.composite_iz)],
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
        Column(""), Column("Element", "L{3cm}"),
        Column("Slenderness Ratio", "C{3.5cm}"),
        Column("Class Limit", "C{2.5cm}"),
        Column("Classification", ">{\\centering\\arraybackslash}p{4.0cm}"),
    ]
    groups = []
    for g in girders:
        c = g.classification
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Top Flange", _fmt_ratio(c.flange_slenderness), _fmt_ratio(c.flange_class_limit), c.class_flange or "---"],
            ["Web", _fmt_ratio(c.web_slenderness), _fmt_ratio(c.web_class_limit), c.class_web or "---"],
            ["Overall Section", "---", "---", c.section_class or "---"],
        ]))
    return Table(caption="Girder Section Classification", columns=cols, groups=groups)


def _build_table_5_3(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.3 — Moment Capacity Check."""
    groups = []
    for g in girders:
        fl = g.flexure
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Applied Moment, $M_u$", "Governing LC (ULS)", _fmt_qv_unit(fl.mu_applied), "---"],
            ["Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", _fmt_qv_unit(fl.md_capacity), "---"],
            ["Utilization Ratio, $M_u / M_d$", "$M_u / M_d$", _fmt_ratio(fl.utilization_ratio), _fmt_status(fl.status)],
        ]))
    return Table(caption="Moment Capacity Check", columns=COLS_5_CHECK, groups=groups)


def _build_table_5_4(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.4 — Shear Capacity Check."""
    groups = []
    for g in girders:
        sh = g.shear
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Applied Shear, $V_u$", "Governing LC (ULS)", _fmt_qv_unit(sh.vu), "---"],
            ["Shear Area, $A_v$", "$d_w \\times t_w$", _fmt_qv_unit(sh.shear_av), "---"],
            ["Panel Aspect Ratio, c/d", "---", _fmt_ratio(sh.panel_cd), "---"],
            ["Shear Buckling Coeff, $k_v$", "IS 800 Cl. 8.4.2.2", _fmt_ratio(sh.shear_kv), "---"],
            ["Web Slenderness, $\\lambda_w$", "$\\sqrt{f_{yw}/(\\sqrt{3}\\,\\tau_{cr})}$", _fmt_ratio(sh.shear_lambda_w), "---"],
            ["Design Shear Stress, $\\tau_b$", "IRC 22 Cl. 603.3.3.2", _fmt_qv_unit(sh.shear_tau_b), "---"],
            ["Shear Buckling Resistance, $V_{cr}$", "$A_v \\times \\tau_b$", _fmt_qv_unit(sh.shear_vcr), "---"],
            ["Utilization Ratio, $V_u / V_d$", "$V_u / V_d$", _fmt_ratio(sh.utilization_ratio), _fmt_status(sh.status)],
        ]))
    return Table(caption="Shear Capacity Check", columns=COLS_5_CHECK, groups=groups)


def _build_table_5_5(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.5 — Interaction Checks (M-V and M-N)."""
    cols = [
        Column(""), Column("Check", "C{3.5cm}"),
        Column("Condition", "C{3.5cm}"),
        Column("Value", ">{\\centering\\arraybackslash}p{4.2cm}"),
        Column("Status", "C{1.8cm}"),
    ]
    groups = []
    for g in girders:
        ix = g.interaction
        # M-N condition string
        if ix.mn_ratio is not None and ix.mn_axial is not None and ix.mn_moment is not None:
            mn_cond = f"{ix.mn_axial:.2f} + {ix.mn_moment:.2f} = {ix.mn_ratio:.3f}"
            mn_val = f"{ix.mn_ratio:.3f}"
        else:
            mn_cond = "N/A"
            mn_val = "N/A"
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["High Shear Condition?", "$V_u > 0.6\\,V_d$", ix.high_shear or "---", "---"],
            ["Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", _fmt_qv_unit(ix.mdv), "---"],
            ["Interaction Check: $M_u \\leq M_{dv}$", "---", _fmt_ratio(ix.mv_ur), _fmt_status(ix.mv_status)],
            ["Interaction Check: $N_u/N_{Rd} + M_u/M_{dv} \\leq 1.0$", mn_cond, mn_val, _fmt_status(ix.mn_status)],
        ]))
    return Table(caption="Interaction Checks (M-V and M-N)", columns=cols, groups=groups)


def _build_table_5_6(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.6 — Lateral Torsional Buckling Check."""
    groups = []
    for g in girders:
        lt = g.ltb
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", _fmt_qv_unit(lt.mcr), "---"],
            ["Non-dim. Slenderness, $\\bar{\\lambda}_{LT}$", "$\\sqrt{M_p / M_{cr}}$", _fmt_ratio(lt.ltb_lambda), "---"],
            ["LTB Reduction Factor, $\\chi_{LT}$", "IS 800 Cl. 8.2.2", _fmt_ratio(lt.ltb_chi), "---"],
            ["LTB Resistance, $M_b$", "$\\chi_{LT}\\,M_p / \\gamma_{m0}$", _fmt_qv_unit(lt.ltb_mb), "---"],
            ["$M_u \\leq M_b$", "$M_u / M_b$", _fmt_ratio(lt.utilization_ratio), _fmt_status(lt.status)],
        ]))
    return Table(caption="Lateral Torsional Buckling Check -- Construction Stage", columns=COLS_5_CHECK, groups=groups)


def _build_table_5_7(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.7 — Stiffener Design Summary."""
    cols = [Column(""), Column("Parameter", "L{6.5cm}"), Column("Value", ">{\\arraybackslash}p{6.5cm}")]
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


def _build_table_5_8(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.8 — Intermediate Stiffener Checks (Custom mode only)."""
    groups = []
    for g in girders:
        if g.intermediate_stiffener is None:
            continue
        ist = g.intermediate_stiffener
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Min. Moment of Inertia, $I_s$", _fmt_qv_unit(ist.iys_min), _fmt_qv_unit(ist.iys_prov), _fmt_status(ist.iys_status)],
            ["Buckling Resistance, $F_{qd} \\geq F_q$", _fmt_qv_unit(ist.fq), _fmt_qv_unit(ist.fqd), _fmt_status(ist.fqd_status)],
        ]))
    return Table(caption="Intermediate Stiffener Checks", columns=COLS_5_REQ, groups=groups)


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
    return Table(caption="End Panel Stiffener Checks", columns=COLS_5_REQ, groups=groups)


def _build_table_5_10(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.10 — Serviceability: Deflection Checks."""
    groups = []
    for g in girders:
        df = g.deflection
        allow_live = _fmt_qv_unit(df.allow_live) if df.allow_live else "---"
        allow_total = _fmt_qv_unit(df.allow_total) if df.allow_total else "---"
        groups.append(TableGroup(label=g.girder_label, rows=[
            ["Live Load Deflection, $\\delta_{LL}$ (mm)", f"L/800 = {allow_live}", _fmt_qv(df.actual_live), _fmt_status(df.live_status)],
            ["Total Load Deflection, $\\delta_{total}$ (mm)", f"L/600 = {allow_total}", _fmt_qv(df.actual_total), _fmt_status(df.total_status)],
        ]))
    return Table(caption="Serviceability -- Deflection Checks", columns=COLS_5_DEF, groups=groups)


def _build_table_5_11(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.11 — Serviceability: Maximum Stress Limitation (flat, no groups)."""
    cols = [
        Column(""), Column("Element", "L{3.5cm}"),
        Column("Allowable Stress", "C{3.5cm}"),
        Column("Actual Stress", ">{\\centering\\arraybackslash}p{3.5cm}"),
        Column("Status", "C{2.5cm}"),
    ]
    rows = []
    for g in girders:
        st = g.stress
        rows.append([
            g.girder_label,
            "Structural Steel ($0.9\\,f_y$)",
            _fmt_qv_unit(st.allowable_stress),
            _fmt_qv_unit(st.actual_stress),
            _fmt_status(st.status),
        ])
    return Table(caption="Serviceability -- Maximum Stress Limitation", columns=cols, rows=rows)


def _build_table_5_12(girders: tuple[GirderDesignData, ...]) -> Table:
    """Table 5.12 — Serviceability: Fatigue Assessment (flat, no groups)."""
    cols = [
        Column(""), Column("Stress Range, $\\Delta\\sigma$ (MPa)", "C{3.5cm}"),
        Column("Fatigue Limit, $f_{fd}$ (MPa)", "C{3.5cm}"),
        Column("Utilization Ratio", ">{\\centering\\arraybackslash}p{3.5cm}"),
        Column("Status", "C{2.5cm}"),
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
    return Table(caption="Serviceability -- Fatigue Assessment", columns=cols, rows=rows)


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
    return Table(caption="Girder Design Summary (DCR / Utilization Ratio)", columns=cols, rows=rows)
    return Table(caption="Girder Design Summary (DCR / Utilization Ratio)", columns=cols, rows=rows)

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
            r"Design Resistance, $Q_u$",
            r"\footnotesize\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[3pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[3pt]$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$}",
            _fmt_qv_unit(sc.design_resistance_qu),
            "IRC 22 Cl. 606.3.1 (Eq. 6.1)"
        ],
        [
            r"Fatigue Shear Resistance, $Q_r$",
            r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
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
    return Table(caption="Shear Connector Spacing", columns=cols, rows=rows)

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
    
    d_val = f"$d$ = {_fmt_qv_unit(sc.stud_diameter)}" if sc.stud_diameter else "$d$ = ---"
    d_lim = f"$\leq 2t_f$ = {_fmt_qv_unit(sc.stud_diameter_limit)}" if sc.stud_diameter_limit else "$\leq 2t_f$ = ---"
    
    edge_prov = f"Provided {_fmt_qv_unit(sc.edge_dist_prov)}" if sc.edge_dist_prov else "Provided ---"
    edge_req = f"(req. $\geq$ {_fmt_qv_unit(sc.edge_dist_req)})" if sc.edge_dist_req else "(req. $\geq$ ---)"

    rows = [
        [r"Longitudinal Shear per unit length, $V_L$", _fmt_qv_unit(sc.vl_longitudinal), "---"],
        [r"Transverse Shear Capacity of Slab, $V_{Rd$}", _fmt_qv_unit(sc.vrd_capacity), "---"],
        [r"Transverse Shear Check", r"$V_L/V_{Rd}$ = " + ts_ur_str, _fmt_status(sc.transverse_status)],
        [r"Min. Transverse Reinforcement, $A_{st,min$}", f"{ast_req_str}, {ast_prov_str}", _fmt_status(sc.reinf_status)],
        [r"Stud Diameter $\leq 2\,t_f$", f"{d_val} {d_lim}", _fmt_status(sc.diameter_status)],
        [r"Stud Edge Distance", f"{edge_prov} {edge_req}", _fmt_status(sc.edge_dist_status)],
    ]
    return Table(caption="Transverse Shear and Detailing Checks", columns=cols, rows=rows)

def _build_table_5_17a(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{7cm}"), Column("Value", ">{\\arraybackslash}p{8.5cm}")]
    ld = dk.loading
    
    rows = [
        [r"Effective Span", _fmt_qv_unit(ld.effective_span)],
        [r"Deck Slab Thickness, $t_s$", _fmt_qv_unit(ld.thickness)],
        [r"Concrete Grade", f"{ld.concrete_grade} ($f_{{ck}}$ = {_fmt_qv_unit(ld.fck)})" if ld.concrete_grade else "---"],
        [r"Reinforcement Grade", f"{ld.reinf_grade} ($f_y$ = {_fmt_qv_unit(ld.fy)})" if ld.reinf_grade else "---"],
        [r"Dead Load (incl. surfacing), $w_{DL$}", _fmt_qv_unit(ld.dead_load)],
        [r"Governing Live Load Vehicle", ld.vehicle if ld.vehicle else "---"],
        [r"Impact Factor (IF)", f"{ld.impact_factor:.3f}" if ld.impact_factor is not None else "---"],
        [r"Wheel Load for local design, $P_w$", _fmt_qv_unit(ld.wheel_load)],
        [r"Tyre Contact Width, $a$", _fmt_qv_unit(ld.tyre_width)],
    ]
    return Table(caption="Deck Slab --- Loading and Geometry", columns=cols, rows=rows)

def _build_table_5_17b(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "C{3.5cm}"), Column("Demand", "C{3.5cm}"), Column("Capacity", ">{\\centering\\arraybackslash}p{4.2cm}"), Column("Status", "C{1.8cm}")]
    fx = dk.flexure
    rows = [
        [r"Sagging (Midspan)", _fmt_qv_unit(fx.demand_sagging), r"$M_{Rd}$ = " + _fmt_qv_unit(fx.capacity_sagging), _fmt_status(fx.status_sagging)],
        [r"Hogging (Support)", _fmt_qv_unit(fx.demand_hogging), r"$M_{Rd}$ = " + _fmt_qv_unit(fx.capacity_hogging), _fmt_status(fx.status_hogging)]
    ]
    return Table(caption="Deck Slab --- Flexure Check: Interior Panel", columns=cols, rows=rows)

def _build_table_5_17c(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{5cm}"), Column("Demand", "C{3.0cm}"), Column("Capacity", "C{3.0cm}"), Column("Status", "C{1.8cm}")]
    fx = dk.flexure
    if not fx.has_overhang:
        rows = [["No Overhang", "N/A", "N/A", "---"]]
    else:
        rows = [
            [r"Overhang Length", _fmt_qv_unit(fx.overhang_length), "---", "---"],
            [r"Total Hogging", _fmt_qv_unit(fx.demand_overhang), r"$M_{Rd,oh}$ = " + _fmt_qv_unit(fx.capacity_overhang), _fmt_status(fx.status_overhang)]
        ]
    return Table(caption="Deck Slab --- Cantilever Overhang Flexure Check", columns=cols, rows=rows)

def _build_table_5_17d(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{5.5cm}"), Column("Formula", "C{3.5cm}"), Column("Value", ">{\\centering\\arraybackslash}p{4.5cm}"), Column("Status", "C{2cm}")]
    sh = dk.shear
    
    ur_str = "---"
    if sh.punching_ur is not None:
        ur_str = f"{sh.punching_ur:.2f}"
    
    rows = [
        [r"Design Wheel Load (ULS), $V_{Ed$}", r"$\gamma_Q\,(1+IF)\,P_w$", _fmt_qv_unit(sh.punching_ved_kn), "---"],
        [r"Punching Shear Stress, $v_{Ed$}", r"$V_{Ed} / (u_1\,d)$", _fmt_qv_unit(sh.punching_ved_mpa), "---"],
        [r"Punching Resistance, $v_{Rd,c$}", r"IRC 112 Eq.\ 10.1", _fmt_qv_unit(sh.punching_vrdc_mpa), "---"],
        [r"Punching Shear Check", r"$v_{Ed} \leq v_{Rd,c}$", ur_str, _fmt_status(sh.punching_status)],
    ]
    return Table(caption="Deck Slab --- Punching Shear Check", columns=cols, rows=rows)

def _build_table_5_17e(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{7cm}"), Column("Value", ">{\\arraybackslash}p{8.5cm}")]
    cw = dk.crack_width
    rows = [
        [r"Max. Permissible Crack Width", _fmt_qv_unit(cw.limit)],
        [r"Calculated Crack Width, $w_k$ (governing)", _fmt_qv_unit(cw.calculated)],
        [r"Crack Width Check", _fmt_status(cw.status)],
    ]
    return Table(caption="Crack Width Check (Deck Slab)", columns=cols, rows=rows)

def _build_table_5_17f(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{5.5cm}"), Column("Formula", "C{3.5cm}"), Column("Value", ">{\\centering\\arraybackslash}p{4.5cm}"), Column("Status", "C{2cm}")]
    sh = dk.shear
    
    ur_str = "---"
    if sh.oneway_ur is not None:
        ur_str = f"{sh.oneway_ur:.2f}"
        
    k_str = f"{sh.oneway_size_factor_k:.3f}" if sh.oneway_size_factor_k is not None else "---"
    rho_str = f"{sh.oneway_rho_l:.4f}" if sh.oneway_rho_l is not None else "---"
        
    rows = [
        [r"Design Shear per unit width, $V_{Ed$}", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$", _fmt_qv_unit(sh.oneway_ved), "---"],
        [r"Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$", k_str, "---"],
        [r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$", rho_str, "---"],
        [r"Shear resistance (no stirrups), $V_{Rd,c$}", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)", _fmt_qv_unit(sh.oneway_vrdc), "---"],
        [r"One-Way Shear Check", r"$V_{Ed} \leq V_{Rd,c}$", ur_str, _fmt_status(sh.oneway_status)],
    ]
    return Table(caption="One-Way (Beam) Shear Check (Deck Slab)", columns=cols, rows=rows)

def _build_table_5_17g(dk: DeckDesignData) -> Table:
    cols = [Column("Parameter", "L{5.5cm}"), Column("Required / Limit", ">{\\centering\\arraybackslash}p{4.1cm}"), Column("Provided", ">{\\centering\\arraybackslash}p{4.1cm}"), Column("Status", "C{1.8cm}")]
    dt = dk.detailing
    rows = [
        [r"Main (Bottom Transverse)", _fmt_qv_unit(dt.required_bottom), _fmt_qv_unit(dt.provided_bottom), _fmt_status(dt.status_bottom)],
        [r"Main (Top Transverse)", _fmt_qv_unit(dt.required_top), _fmt_qv_unit(dt.provided_top), _fmt_status(dt.status_top)],
        [r"Distribution (Longitudinal)", _fmt_qv_unit(dt.required_dist), _fmt_qv_unit(dt.provided_dist), _fmt_status(dt.status_dist)],
    ]
    return Table(caption="Reinforcement Detailing Summary (Deck Slab)", columns=cols, rows=rows)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Phase 5C: Cross Bracing, End Diaphragm, and Overall Summary
# ---------------------------------------------------------------------------

def _build_table_5_20a(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel"), Column("Member"), Column("Connection"), Column("Section"),
        Column("$A_g$ (mm$^2$)"), Column("$r_{min}$ (mm)")
    ]
    if not cb or not cb.panels:
        return Table(caption="End Diaphragm --- Connection and Section Properties", columns=cols, rows=[["---"] * 6])
    
    rows = []
    for p in cb.panels:
        for m_name, m_label in [("diagonal", "Diagonal"), ("chord", "Chord")]:
            mem = p.diagonal_tension if m_name == "diagonal" else p.chord_tension
            if not mem: mem = p.diagonal_compression if m_name == "diagonal" else p.chord_compression
            if not mem: continue
            
            rows.append([
                p.pair_label, m_label, mem.connection_type or "---", mem.section or "---",
                "---", "---"  # Ag and rmin are not currently preserved by legacy extract
            ])
            
    return Table(caption=r"\textbf{Cross Bracing --- Connection and Section Properties}", columns=cols, rows=rows)

def _build_table_5_20b(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel"), Column("Member"), Column("Nature"),
        Column("Eff. Length $KL$ (mm)"), Column("$KL/r$"), Column("Limit / Status")
    ]
    if not cb or not cb.panels:
        return Table(caption="End Diaphragm --- Slenderness Ratio Check", columns=cols, rows=[["---"] * 6])
    
    rows = []
    for p in cb.panels:
        ur_str = f"{p.slenderness_ur:.2f}" if p.slenderness_ur is not None else "---"
        rows.append([p.pair_label, "---", "---", "---", "---", f"UR={ur_str} " + _fmt_status(p.slenderness_status)])
        
    return Table(caption=r"\textbf{Cross Bracing --- Slenderness Ratio Check}", columns=cols, rows=rows)

def _build_table_5_20c(cb: CrossBracingData | None) -> Table:
    cols = [
        Column("Panel"), Column("Member"), Column("Section"),
        Column("Governing LC"), Column("Demand (kN)"), Column("Capacity (kN)"),
        Column("UR"), Column("Status")
    ]
    if not cb or not cb.panels:
        return Table(caption=r"\textbf{Cross Bracing Design --- Capacity Summary}", columns=cols, rows=[["---"] * 8])
        
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
        
    return Table(caption=r"\textbf{Cross Bracing Design --- Capacity Summary}", columns=cols, rows=rows)

def _build_table_5_21(ed: EndDiaphragmData | None) -> Table:
    cols = [
        Column("Panel"), Column("Member"), Column("Section"),
        Column("Governing LC"), Column("Demand (kN)"), Column("Capacity (kN)"),
        Column("UR"), Column("Status")
    ]
    if not ed or not ed.panels:
        return Table(caption=r"\textbf{End Diaphragm Design --- Capacity Summary}", columns=cols, rows=[["---"] * 8])
        
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
        
    return Table(caption=r"\textbf{End Diaphragm Design --- Capacity Summary}", columns=cols, rows=rows)

def _build_table_5_22(summary: OverallSummaryData | None) -> Table:
    cols = [
        Column("Check / Member", "L{4.5cm}"), Column("Governing LC", "L{5.0cm}"),
        Column("Demand"), Column("Capacity"), Column("UR", "C{1.5cm}"), Column("Status")
    ]
    if not summary:
        return Table(caption="Overall Design Check Summary", columns=cols, rows=[["---"] * 6])
        
    rows = []
    for comp in (summary.girders, summary.deck, summary.cross_bracing, summary.end_diaphragm):
        if not comp: continue
        for r in comp.records:
            rows.append([
                r.label,
                r.governing_lc or "---",
                _fmt_qv_unit(r.demand),
                _fmt_qv_unit(r.capacity),
                _fmt_ratio(r.ur),
                _fmt_status(r.status)
            ])
            
    return Table(
        caption=r"\textbf{Overall Design Check Summary (Table 5.22)}",
        columns=cols,
        rows=rows,
        label="tab:ch5_overall_summary"
    )

def build_chapter_5(facts: ReportFacts) -> Chapter:
    """Build Chapter 5: Design Checks.

    If ``facts.design_check_data`` is available (Phase 5A), builds semantic
    Tables 5.1–5.13 from typed GirderDesignData.  Otherwise falls back to the
    legacy adapter for any remaining non-migrated tables.
    """
    components = []

    if facts.design_check_data is not None:
        gd = facts.design_check_data
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
                components.append(tbl)
                components.append(RawLatex(r"\vspace{1em}"))
        
        if gd.shear_connectors:
            sc = gd.shear_connectors
            components.append(_build_table_5_14(sc))
            components.append(RawLatex(r"\vspace{1em}"))
            
            from ..document import LayoutHints
            
            # Needspace hack before table 5.15
            t515 = _build_table_5_15(sc)
            components.append(t515)
            components.append(RawLatex(r"\noindent\textit{Note: IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.}"))
            components.append(RawLatex(r"\vspace{1em}"))
            
            t516 = _build_table_5_16(sc)
            components.append(t516)
            components.append(RawLatex(r"\noindent\textit{Note: IRC 22 Cl. 606.6, 606.10.}"))
            components.append(RawLatex(r"\vspace{1em}"))
            
        if gd.deck and gd.deck.is_designed:
            dk = gd.deck
            components.append(_build_table_5_17a(dk))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_17b(dk))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_17c(dk))
            components.append(RawLatex(r"\vspace{1em}"))
            
            t17d = _build_table_5_17d(dk)
            components.append(t17d)
            components.append(RawLatex(r"\noindent\textit{Note: Punching shear reinforcement not typically required for deck slabs with $d \geq 200$ mm and adequate longitudinal reinforcement.}"))
            components.append(RawLatex(r"\vspace{1em}"))
            
            components.append(_build_table_5_17e(dk))
            components.append(RawLatex(r"\vspace{1em}"))
            
            t17f = _build_table_5_17f(dk)
            components.append(t17f)
            components.append(RawLatex(r"\noindent\textit{Note: IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on concrete and main reinforcement.}"))
            components.append(RawLatex(r"\vspace{1em}"))
            
            components.append(_build_table_5_17g(dk))
            components.append(RawLatex(r"\vspace{1em}"))
            

        cb = gd.cross_bracing
        ed = gd.end_diaphragm
        summary = gd.summary
        
        if cb and cb.panels:
            components.append(RawLatex(r"\section{Cross Bracing Design}"))
            components.append(RawLatex(r"\label{sec:cross-bracing}"))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_20a(cb))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_20b(cb))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_20c(cb))
            components.append(RawLatex(r"\vspace{1em}"))
            
        if ed:
            components.append(RawLatex(r"\section{End Diaphragm Design}"))
            components.append(RawLatex(r"\label{sec:end-diaphragm}"))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_21(ed))
            components.append(RawLatex(r"\vspace{1em}"))
            
        if summary:
            components.append(RawLatex(r"\section{Overall Design Check Summary}"))
            components.append(RawLatex(r"\label{sec:overall-summary}"))
            components.append(RawLatex(r"\vspace{1em}"))
            components.append(_build_table_5_22(summary))
            components.append(RawLatex(r"\vspace{4.0mm}"))
            if summary.end_diaphragm and summary.end_diaphragm.status == CheckStatus.UNAVAILABLE:
                components.append(RawLatex(r"\noindent\textit{Note: End Diaphragm rolled/welded section design to be added.}"))
            components.append(RawLatex(r"\vspace{1em}"))
    else:
        # Fallback: delegate to legacy ch5_design_checks
        from osdagbridge.core.reports.chap5 import ch5_design_checks
        from osdagbridge.core.reports.report_generator import ReportDataBridge

        input_dict = facts.raw_input_dict or {}
        output_dict = facts.raw_output_dict or {}

        bridge = ReportDataBridge(output_dict, input_dict, _PayloadProxy(facts))
        latex = ch5_design_checks(facts.design_checks or [], bridge)
        components.append(RawLatex(latex))

    return Chapter(
        number=5,
        title="Design Checks",
        sections=[Section(title="", level=2, components=components)],
    )


class _PayloadProxy:
    """Minimal proxy satisfying the ReportPayload interface accessed by
    ReportDataBridge -- only ``design_checks`` is read."""

    def __init__(self, facts: ReportFacts):
        self.design_checks = facts.design_checks or []
