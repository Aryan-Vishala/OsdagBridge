"""Extraction functions for design check data (Chapter 5).

Phase 5A: girder design tables (5.1–5.13) only.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from osdagbridge.core.utils import common as c
from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MDV,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR,
)

from . import (
    CheckStatus,
    DesignCheckData,
    GirderClassification,
    GirderDeflectionCheck,
    GirderDesignData,
    GirderDesignSummary,
    GirderFatigueCheck,
    GirderFlexureCheck,
    GirderIntermediateStiffenerCheck,
    GirderInteractionCheck,
    GirderLTBCheck,
    GirderSectionProperties,
    GirderShearCheck,
    GirderBearingStiffenerCheck,
    GirderStiffenerSummary,
    GirderStressCheck,
    QuantityValue,
    ShearConnectorSpacing,
    ShearConnectorData,
    DeckLoadingGeometry,
    DeckFlexureCheck,
    DeckShearCheck,
    DeckCrackWidthCheck,
    DeckDetailingCheck,
    DeckDesignData,
    BracingMemberCheck,
    BracingPanelData,
    CrossBracingData,
    EndDiaphragmData,
    SummaryCheckRecord,
    ComponentSummary,
    OverallSummaryData,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(val: Optional[object]) -> Optional[float]:
    """Convert a value to float, returning None if not possible."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_int(val: Optional[object]) -> Optional[int]:
    """Convert a value to int, returning None if not possible."""
    if val is None:
        return None
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def _qv(value: Optional[object], unit: str = "") -> Optional[QuantityValue]:
    """Create a QuantityValue from a raw value, or None."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return QuantityValue(value=f, unit=unit)


def _get(d: dict, key: str) -> Optional[object]:
    """Safe dict.get — returns None for missing/None values."""
    v = d.get(key)
    return v if v is not None else None


def _interaction_status(ratio: Optional[float]) -> CheckStatus:
    """IS 800 interaction threshold: <0.90 PASS, <1.00 WARN, >=1.00 FAIL."""
    if ratio is None:
        return CheckStatus.UNAVAILABLE
    if ratio < 0.90:
        return CheckStatus.PASS
    elif ratio < 1.00:
        return CheckStatus.WARN
    return CheckStatus.FAIL


def _ur_status(ratio: Optional[float]) -> CheckStatus:
    """Simple UR threshold: <=1.0 PASS, >1.0 FAIL."""
    if ratio is None:
        return CheckStatus.UNAVAILABLE
    return CheckStatus.PASS if ratio <= 1.0 else CheckStatus.FAIL


def _ge_status(provided: Optional[float], required: Optional[float]) -> CheckStatus:
    """Provided >= Required → PASS."""
    if provided is None or required is None:
        return CheckStatus.UNAVAILABLE
    return CheckStatus.PASS if provided >= required else CheckStatus.FAIL


def _le_status(actual: Optional[float], limit: Optional[float]) -> CheckStatus:
    """Actual <= Limit → PASS."""
    if actual is None or limit is None:
        return CheckStatus.UNAVAILABLE
    return CheckStatus.PASS if actual <= limit else CheckStatus.FAIL


def _parse_status_string(raw: Optional[str]) -> CheckStatus:
    """Parse an engine-provided status string like 'PASS'/'FAIL'."""
    if raw is None:
        return CheckStatus.UNAVAILABLE
    s = str(raw).strip().lower()
    if "fail" in s:
        return CheckStatus.FAIL
    if "pass" in s:
        return CheckStatus.PASS
    if "warn" in s:
        return CheckStatus.WARN
    return CheckStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Girder label helpers
# ---------------------------------------------------------------------------


def _girder_entries(input_dict: dict) -> list[tuple[str, str]]:
    """Retrieve girder labels and member IDs from input_dict."""
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))
    if n <= 0:
        n = 1
    from osdagbridge.core.utils.common import (
        KEY_MP_GD_MEMBER_ID,
        KEY_MP_GD_SELECT_GIRDER,
    )

    entries = []
    for i in range(1, n + 1):
        lbl = input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", f"G{i}")
        mid = input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", f"G{i}M1")
        entries.append((lbl, mid))
    return entries


# ---------------------------------------------------------------------------
# Table 5.1 — Girder Section Properties
# ---------------------------------------------------------------------------


def _build_section_properties(
    od: dict, lbl: str
) -> GirderSectionProperties:
    return GirderSectionProperties(
        girder_label=lbl,
        depth=_qv(_get(od, KEY_SD_TOTAL_DEPTH), "mm"),
        top_flange_width=_qv(_get(od, KEY_SD_TOP_FLANGE_WIDTH), "mm"),
        bottom_flange_width=_qv(_get(od, KEY_SD_BOTTOM_FLANGE_WIDTH), "mm"),
        top_flange_thickness=_qv(_get(od, KEY_SD_TOP_FLANGE_THICKNESS), "mm"),
        bottom_flange_thickness=_qv(_get(od, KEY_SD_BOTTOM_FLANGE_THICKNESS), "mm"),
        web_thickness=_qv(_get(od, KEY_SD_WEB_THICKNESS), "mm"),
        gross_area=_qv(_get(od, KEY_SD_SECTION_PROP_AREA), "cm\u00b2"),
        moment_of_inertia=_qv(_get(od, KEY_SD_SECTION_PROP_IZ), "cm\u2074"),
        elastic_section_modulus=_qv(_get(od, KEY_SD_SECTION_PROP_ZZ), "cm\u00b3"),
        plastic_section_modulus=_qv(_get(od, KEY_SD_SECTION_PROP_ZUZ), "cm\u00b3"),
        effective_slab_width=_qv(_get(od, KEY_SD_EFFECTIVE_SLAB_WIDTH), "mm"),
        composite_iz=_qv(_get(od, KEY_SD_COMPOSITE_IZ), "cm\u2074"),
        pna_depth=_qv(_get(od, KEY_SD_PNA_DEPTH), "mm"),
    )


# ---------------------------------------------------------------------------
# Table 5.2 — Section Classification
# ---------------------------------------------------------------------------


def _build_classification(od: dict) -> GirderClassification:
    return GirderClassification(
        flange_slenderness=_safe_float(_get(od, KEY_SD_FLANGE_SLENDERNESS)),
        flange_class_limit=_safe_float(_get(od, KEY_SD_FLANGE_CLASS_LIMIT)),
        class_flange=str(od.get(KEY_SD_CLASS_FLANGE, "") or ""),
        web_slenderness=_safe_float(_get(od, KEY_SD_WEB_SLENDERNESS)),
        web_class_limit=_safe_float(_get(od, KEY_SD_WEB_CLASS_LIMIT)),
        class_web=str(od.get(KEY_SD_CLASS_WEB, "") or ""),
        section_class=str(od.get(KEY_SD_SECTION_CLASS, "") or ""),
    )


# ---------------------------------------------------------------------------
# Table 5.3 — Moment Capacity Check
# ---------------------------------------------------------------------------


def _build_flexure_check(od: dict) -> GirderFlexureCheck:
    ur_pct = _safe_float(_get(od, KEY_UTIL_FLEXURE))
    ur = ur_pct / 100.0 if ur_pct is not None else None
    return GirderFlexureCheck(
        mu_applied=_qv(_get(od, KEY_SD_MU_APPLIED), "kN-m"),
        md_capacity=_qv(_get(od, KEY_SD_MD_CAPACITY), "kN-m"),
        utilization_ratio=ur,
        status=_ur_status(ur),
    )


# ---------------------------------------------------------------------------
# Table 5.4 — Shear Capacity Check
# ---------------------------------------------------------------------------


def _build_shear_check(od: dict) -> GirderShearCheck:
    ur_pct = _safe_float(_get(od, KEY_UTIL_SHEAR))
    ur = ur_pct / 100.0 if ur_pct is not None else None
    return GirderShearCheck(
        vu=_qv(_get(od, KEY_SD_SHEAR_VU), "kN"),
        shear_av=_qv(_get(od, KEY_SD_SHEAR_AV), "mm\u00b2"),
        panel_cd=_safe_float(_get(od, KEY_SD_PANEL_CD)),
        shear_kv=_safe_float(_get(od, KEY_SD_SHEAR_KV)),
        shear_lambda_w=_safe_float(_get(od, KEY_SD_SHEAR_LAMBDA_W)),
        shear_tau_b=_qv(_get(od, KEY_SD_SHEAR_TAU_B), "MPa"),
        shear_vcr=_qv(_get(od, KEY_SD_SHEAR_VCR), "kN"),
        utilization_ratio=ur,
        status=_ur_status(ur),
    )


# ---------------------------------------------------------------------------
# Table 5.5 — Interaction Checks (M-V and M-N)
# ---------------------------------------------------------------------------


def _build_interaction_check(od: dict) -> GirderInteractionCheck:
    mv_ur_pct = _safe_float(_get(od, KEY_UTIL_INTERACTION))
    mv_ur = mv_ur_pct / 100.0 if mv_ur_pct is not None else None
    mn_ratio = _safe_float(_get(od, KEY_SD_MN_RATIO))
    return GirderInteractionCheck(
        high_shear=str(od.get(KEY_SD_HIGH_SHEAR, "") or ""),
        mdv=_qv(_get(od, KEY_SD_MDV), "kN-m"),
        mv_ur=mv_ur,
        mv_status=_interaction_status(mv_ur),
        mn_axial=_safe_float(_get(od, KEY_SD_MN_AXIAL)),
        mn_moment=_safe_float(_get(od, KEY_SD_MN_MOMENT)),
        mn_ratio=mn_ratio,
        mn_status=_interaction_status(mn_ratio),
    )


# ---------------------------------------------------------------------------
# Table 5.6 — Lateral Torsional Buckling
# ---------------------------------------------------------------------------


def _build_ltb_check(od: dict) -> GirderLTBCheck:
    ur_pct = _safe_float(_get(od, KEY_UTIL_LTB))
    ur = ur_pct / 100.0 if ur_pct is not None else None
    return GirderLTBCheck(
        mcr=_qv(_get(od, KEY_SD_LTB_MCR), "kN-m"),
        ltb_lambda=_safe_float(_get(od, KEY_SD_LTB_LAMBDA)),
        ltb_chi=_safe_float(_get(od, KEY_SD_LTB_CHI)),
        ltb_mb=_qv(_get(od, KEY_SD_LTB_MB), "kN-m"),
        utilization_ratio=ur,
        status=_interaction_status(ur),
    )


# ---------------------------------------------------------------------------
# Table 5.7 — Stiffener Design Summary
# ---------------------------------------------------------------------------


def _build_stiffener_summary(od: dict) -> GirderStiffenerSummary:
    return GirderStiffenerSummary(
        method=str(od.get(KEY_SD_STIFF_METHOD, "") or ""),
        int_thick=_qv(_get(od, KEY_SD_STIFF_INT_THICK), "mm"),
        int_spacing=_qv(_get(od, KEY_SD_STIFF_INT_SPACING), "mm"),
        end_thick=_qv(_get(od, KEY_SD_STIFF_END_THICK), "mm"),
        end_count=_safe_int(_get(od, KEY_SD_STIFF_END_COUNT)),
        long_stiff=str(od.get(KEY_SD_STIFF_LONG, "") or ""),
    )


# ---------------------------------------------------------------------------
# Table 5.8 — Intermediate Stiffener Checks (Custom mode only)
# ---------------------------------------------------------------------------


def _build_intermediate_stiffener_check(
    od: dict,
) -> Optional[GirderIntermediateStiffenerCheck]:
    iys_min = _safe_float(_get(od, KEY_SD_IS_IYS_MIN))
    iys_prov = _safe_float(_get(od, KEY_SD_IS_IYS_PROV))
    fq = _safe_float(_get(od, KEY_SD_IS_FQ))
    fqd = _safe_float(_get(od, KEY_SD_IS_FQD))
    if iys_min is None and iys_prov is None and fq is None and fqd is None:
        return None
    return GirderIntermediateStiffenerCheck(
        iys_min=_qv(iys_min, "mm\u2074"),
        iys_prov=_qv(iys_prov, "mm\u2074"),
        iys_status=_ge_status(iys_prov, iys_min),
        fq=_qv(fq, "kN"),
        fqd=_qv(fqd, "kN"),
        fqd_status=_ge_status(fqd, fq),
    )


# ---------------------------------------------------------------------------
# Table 5.9 — End Panel Stiffener Checks
# ---------------------------------------------------------------------------


def _build_bearing_stiffener_check(od: dict) -> GirderBearingStiffenerCheck:
    r = _safe_float(_get(od, KEY_SD_BS_R))

    def _pair(resist_key: str) -> tuple[
        Optional[float], Optional[float], CheckStatus
    ]:
        prov = _safe_float(_get(od, resist_key))
        if prov is None or prov <= 0.0 or r is None:
            return (r, prov, CheckStatus.UNAVAILABLE)
        return (r, prov, _ge_status(prov, r))

    wb_r, wb_p, wb_s = _pair(KEY_SD_BS_FCDW_WB)
    lc_r, lc_p, lc_s = _pair(KEY_SD_BS_FCDW_LC)
    ps_r, ps_p, ps_s = _pair(KEY_SD_BS_FPSD)
    cb_r, cb_p, cb_s = _pair(KEY_SD_BS_FCD)
    return GirderBearingStiffenerCheck(
        wb_req=_qv(wb_r, "kN"),
        wb_prov=_qv(wb_p, "kN"),
        wb_status=wb_s,
        lc_req=_qv(lc_r, "kN"),
        lc_prov=_qv(lc_p, "kN"),
        lc_status=lc_s,
        ps_req=_qv(ps_r, "kN"),
        ps_prov=_qv(ps_p, "kN"),
        ps_status=ps_s,
        cb_req=_qv(cb_r, "kN"),
        cb_prov=_qv(cb_p, "kN"),
        cb_status=cb_s,
    )


# ---------------------------------------------------------------------------
# Table 5.10 — Deflection Checks
# ---------------------------------------------------------------------------


def _build_deflection_check(
    od: dict, input_dict: dict, gi: int
) -> GirderDeflectionCheck:
    span_m = _safe_float(_get(input_dict, KEY_SPAN)) or 0.0
    allow_live = span_m * 1000.0 / 800.0 if span_m else None
    allow_total = span_m * 1000.0 / 600.0 if span_m else None

    actual_live = _safe_float(_get(od, f"{KEY_SD_DEFL_LIVE}.G{gi}"))
    actual_total = _safe_float(_get(od, f"{KEY_SD_DEFL_TOTAL}.G{gi}"))

    return GirderDeflectionCheck(
        allow_live=_qv(allow_live, "mm"),
        allow_total=_qv(allow_total, "mm"),
        actual_live=_qv(actual_live, "mm"),
        actual_total=_qv(actual_total, "mm"),
        live_status=_le_status(actual_live, allow_live),
        total_status=_le_status(actual_total, allow_total),
    )


# ---------------------------------------------------------------------------
# Table 5.11 — Stress Limitation
# ---------------------------------------------------------------------------


def _build_stress_check(od: dict) -> GirderStressCheck:
    dr = od.get("design_results", {}) or {}
    actual = _safe_float(_get(dr, "steeldesign.stress.steel"))
    allow = _safe_float(_get(dr, "steeldesign.stress.steel.allowable"))
    return GirderStressCheck(
        allowable_stress=_qv(allow, "MPa"),
        actual_stress=_qv(actual, "MPa"),
        status=_le_status(actual, allow),
    )


# ---------------------------------------------------------------------------
# Table 5.12 — Fatigue Assessment
# ---------------------------------------------------------------------------


def _build_fatigue_check(od: dict, gi: int) -> GirderFatigueCheck:
    dr = od.get("design_results", {}) or {}
    uls = dr.get("steeldesign.uls_per_girder", {}) or {}
    fat = uls.get("fatigue", {}) or {}
    g = fat.get(f"G{gi}", {}) or {}
    demand = _safe_float(g.get("demand"))
    capacity = _safe_float(g.get("capacity"))
    ur = _safe_float(g.get("ur"))
    if ur is not None and demand is not None and capacity is not None:
        pass  # ur already from engine
    elif demand is not None and capacity is not None and capacity > 0:
        ur = demand / capacity
    return GirderFatigueCheck(
        stress_range=_qv(demand, "MPa"),
        fatigue_limit=_qv(capacity, "MPa"),
        utilization_ratio=ur,
        status=_parse_status_string(g.get("status")),
    )


# ---------------------------------------------------------------------------
# Table 5.13 — Girder Design Summary
# ---------------------------------------------------------------------------


def _build_girder_summary(od: dict, gi: int) -> GirderDesignSummary:
    dr = od.get("design_results", {}) or {}
    pg = dr.get("per_girder", {}) or {}
    g = pg.get(f"G{gi}", {}) or {}
    checks = g.get("checks") or []
    per_lc = g.get("per_lc") or {}

    if not checks:
        fallback_lc = g.get("demand", {}).get("governing_combination", "")
        return GirderDesignSummary(
            governing_lc=str(fallback_lc),
            status=CheckStatus.UNAVAILABLE,
        )

    ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
    ctrl_lc = ""
    best_dcr: Optional[float] = None
    for lc_name, lc_data in per_lc.items():
        if str(lc_name).lower().startswith("envelope"):
            continue
        for chk in lc_data.get("checks") or []:
            if chk.get("id") == ctrl.get("check_id"):
                d = chk.get("dcr") or 0.0
                if best_dcr is None or d > best_dcr:
                    best_dcr = d
                    ctrl_lc = lc_name

    demand_val = _safe_float(ctrl.get("demand"))
    cap_val = _safe_float(ctrl.get("capacity"))
    return GirderDesignSummary(
        governing_lc=str(ctrl_lc),
        controlling_check=str(ctrl.get("name", "")),
        demand=_qv(demand_val, str(ctrl.get("demand_unit", ""))),
        capacity=_qv(cap_val, str(ctrl.get("capacity_unit", ""))),
        dcr=_safe_float(ctrl.get("dcr")),
        status=_parse_status_string(ctrl.get("status")),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_girder_design_data(
    output_dict: dict,
    input_dict: dict,
) -> tuple[GirderDesignData, ...]:
    """Extract girder design check data from output_dict + input_dict."""
    od = output_dict
    entries = _girder_entries(input_dict)
    is_custom = (
        str(input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower()
        in {"custom", "customized"}
    )

    girders: list[GirderDesignData] = []
    for gi, (lbl, _mid) in enumerate(entries, start=1):
        section_props = _build_section_properties(od, lbl)
        classification = _build_classification(od)
        flexure = _build_flexure_check(od)
        shear = _build_shear_check(od)
        interaction = _build_interaction_check(od)
        ltb = _build_ltb_check(od)
        stiff_summary = _build_stiffener_summary(od)
        int_stiffener = (
            _build_intermediate_stiffener_check(od) if is_custom else None
        )
        bearing_stiffener = _build_bearing_stiffener_check(od)
        deflection = _build_deflection_check(od, input_dict, gi)
        stress = _build_stress_check(od)
        fatigue = _build_fatigue_check(od, gi)
        summary = _build_girder_summary(od, gi)

        girders.append(
            GirderDesignData(
                girder_label=lbl,
                section_properties=section_props,
                classification=classification,
                flexure=flexure,
                shear=shear,
                interaction=interaction,
                ltb=ltb,
                stiffener_summary=stiff_summary,
                intermediate_stiffener=int_stiffener,
                bearing_stiffener=bearing_stiffener,
                deflection=deflection,
                stress=stress,
                fatigue=fatigue,
                summary=summary,
            )
        )

    return tuple(girders)

def build_shear_connector_data(
    output_dict: dict,
    input_dict: dict,
) -> Optional[ShearConnectorData]:
    """Extract Shear Connector data (Tables 5.14-5.16)."""
    from osdagbridge.core.utils.common import (
        KEY_SD_SC_Qu_kN, KEY_SD_SC_Qr_kN,
        KEY_SD_SC_SL1, KEY_SD_SC_SL2, KEY_SD_SC_SR,
        KEY_SD_TS_VL, KEY_SD_TS_VRD,
        KEY_SD_SC_D_LIMIT, KEY_SD_SC_EDGE_DIST, KEY_SD_SC_REQ_EDGE_DIST,
        KEY_DS_STUD_DIAMETER
    )
    
    dr = output_dict.get("design_results", {}) or {}
    
    # Check if SC was run (Qu exists)
    if KEY_SD_SC_Qu_kN not in dr:
        return None

    qu = _safe_float(dr.get(KEY_SD_SC_Qu_kN))
    qr = _safe_float(dr.get(KEY_SD_SC_Qr_kN))

    sc_prov = _safe_float(dr.get("stud_spacing_provided_mm"))
    sc_prov_qv = _qv(sc_prov, "mm")

    def _sp(req_val):
        rv = _safe_float(req_val)
        status = CheckStatus.UNAVAILABLE
        if rv is not None and sc_prov is not None:
            status = CheckStatus.PASS if sc_prov <= rv else CheckStatus.FAIL
        return ShearConnectorSpacing(required=_qv(rv, "mm"), provided=sc_prov_qv, status=status)

    sl1 = _sp(dr.get(KEY_SD_SC_SL1))
    sl2 = _sp(dr.get(KEY_SD_SC_SL2))
    sr = _sp(dr.get(KEY_SD_SC_SR))
    smax = _sp(dr.get("stud_spacing_max_mm"))

    vl = _safe_float(dr.get(KEY_SD_TS_VL))
    vrd = _safe_float(dr.get(KEY_SD_TS_VRD))
    
    ts_ur = None
    if vl is not None and vrd is not None and vrd > 0:
        ts_ur = vl / vrd
        
    ts_ok = dr.get("transverse_shear_ok")
    if ts_ok is True:
        ts_status = CheckStatus.PASS
    elif ts_ok is False:
        ts_status = CheckStatus.FAIL
    else:
        ts_status = CheckStatus.UNAVAILABLE

    ast_req = _safe_float(dr.get("Ast_required_cm2_per_m"))
    
    dd_516 = output_dict.get("deck_design_results", {}) or {}
    ast_prov = None
    try:
        bot = float(dd_516.get("rebar_bottom_area") or 0)
        top = float(dd_516.get("rebar_top_area") or 0)
        ast_prov = (bot + top) / 100.0
    except (TypeError, ValueError):
        pass

    reinf_status = CheckStatus.UNAVAILABLE
    if ast_req is not None and ast_prov is not None:
        reinf_status = CheckStatus.PASS if ast_prov >= ast_req else CheckStatus.FAIL

    stud_d = _safe_float(input_dict.get(KEY_DS_STUD_DIAMETER))
    d_lim = _safe_float(dr.get(KEY_SD_SC_D_LIMIT))
    diam_status = CheckStatus.UNAVAILABLE
    if stud_d is not None and d_lim is not None:
        diam_status = CheckStatus.PASS if stud_d <= d_lim else CheckStatus.FAIL

    edge_prov = _safe_float(dr.get(KEY_SD_SC_EDGE_DIST))
    edge_req = _safe_float(dr.get(KEY_SD_SC_REQ_EDGE_DIST))
    edge_status = CheckStatus.UNAVAILABLE
    if edge_prov is not None and edge_req is not None:
        edge_status = CheckStatus.PASS if edge_prov >= edge_req else CheckStatus.FAIL

    return ShearConnectorData(
        design_resistance_qu=_qv(qu, "kN"),
        fatigue_resistance_qr=_qv(qr, "kN"),
        uls_shear=sl1,
        full_composite=sl2,
        sls_fatigue=sr,
        max_limit=smax,
        vl_longitudinal=_qv(vl, "kN/m"),
        vrd_capacity=_qv(vrd, "kN/m"),
        transverse_ur=ts_ur,
        transverse_status=ts_status,
        min_transverse_reinf_req=_qv(ast_req, "cm^2/m"),
        min_transverse_reinf_prov=_qv(ast_prov, "cm^2/m"),
        reinf_status=reinf_status,
        stud_diameter=_qv(stud_d, "mm"),
        stud_diameter_limit=_qv(d_lim, "mm"),
        diameter_status=diam_status,
        edge_dist_prov=_qv(edge_prov, "mm"),
        edge_dist_req=_qv(edge_req, "mm"),
        edge_dist_status=edge_status
    )

def build_deck_design_data(
    output_dict: dict,
    input_dict: dict,
) -> Optional[DeckDesignData]:
    """Extract Deck Design data (Tables 5.17a-g)."""
    from osdagbridge.core.utils import common as c
    
    deck_rpt = output_dict.get("deck_report_values", {}) or {}
    is_designed = bool(deck_rpt)
    
    if not is_designed:
        return DeckDesignData(is_designed=False)
        
    def _dkv(key, default=0.0):
        v = deck_rpt.get(key)
        if v is None or v == "":
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # --- Loading Geometry ---
    loading = DeckLoadingGeometry(
        effective_span=_qv(_dkv(c.KEY_DD_SPAN), "m"),
        thickness=_qv(_safe_float(input_dict.get(c.KEY_TS_DECK_THICKNESS)), "mm"),
        concrete_grade=str(input_dict.get(c.KEY_DECK_CONCRETE_GRADE_BASIC) or ""),
        fck=None, # chap5.py shows fck is derived inside IRC112, but we don't display it directly? Wait, legacy says `Concrete Grade: M40`. It doesn't show fck.
        reinf_grade=str(input_dict.get(c.KEY_DS_REINF_MATERIAL) or ""),
        fy=_qv(_dkv(c.KEY_DD_FY), "MPa"),
        dead_load=_qv(_dkv(c.KEY_DD_WDL), "kN/m^2"),
        wheel_load=_qv(_dkv(c.KEY_DD_WHEEL_LOAD), "kN"),
        tyre_width=_qv(_dkv(c.KEY_DD_TYRE_WIDTH, 0.0) * 1000.0, "mm"),
        impact_factor=_dkv(c.KEY_DD_IMPACT_FACTOR, 1.0) - 1.0, # 1 + IF is stored
        vehicle=str(deck_rpt.get(c.KEY_DD_VEHICLE) or "")
    )
    
    # --- Flexure Check ---
    has_oh = bool(deck_rpt.get(c.KEY_DD_HAS_OVERHANG))
    m_sag_dem = _dkv(c.KEY_DD_M_ULS_SAG)
    m_sag_cap = _dkv(c.KEY_DD_MU_BOT)
    sag_status = CheckStatus.PASS if m_sag_cap >= m_sag_dem else CheckStatus.FAIL
    
    m_hog_dem = _dkv(c.KEY_DD_M_ULS_HOG)
    m_hog_cap = _dkv(c.KEY_DD_MU_TOP)
    hog_status = CheckStatus.PASS if m_hog_cap >= m_hog_dem else CheckStatus.FAIL
    
    oh_dem = _dkv(c.KEY_DD_M_ULS_OH) if has_oh else None
    oh_cap = _dkv(c.KEY_DD_MU_OH) if has_oh else None
    oh_status = CheckStatus.UNAVAILABLE
    if has_oh and oh_dem is not None and oh_cap is not None:
        oh_status = CheckStatus.PASS if oh_cap >= oh_dem else CheckStatus.FAIL

    flexure = DeckFlexureCheck(
        demand_sagging=_qv(m_sag_dem, "kNm/m"),
        capacity_sagging=_qv(m_sag_cap, "kNm/m"),
        status_sagging=sag_status,
        demand_hogging=_qv(m_hog_dem, "kNm/m"),
        required_top_steel=_qv(_dkv(c.KEY_DD_AS_REQ_TOP), "mm^2/m"),
        capacity_hogging=_qv(m_hog_cap, "kNm/m"),
        status_hogging=hog_status,
        has_overhang=has_oh,
        overhang_length=_qv(_safe_float(input_dict.get(c.KEY_TS_DECK_OVERHANG)), "mm"),
        demand_overhang=_qv(oh_dem, "kNm/m"),
        capacity_overhang=_qv(oh_cap, "kNm/m"),
        status_overhang=oh_status
    )
    
    # --- Shear Check ---
    punch_vrdc = _dkv(c.KEY_DD_VRD_C_MPA)
    punch_ved = _dkv(c.KEY_DD_PUNCH_VED)
    punch_ur = punch_ved / punch_vrdc if punch_vrdc > 0 else None
    punch_ok = deck_rpt.get(c.KEY_DD_PUNCH_OK)
    punch_status = CheckStatus.PASS if punch_ok else CheckStatus.FAIL
    
    ow_ved = _dkv(c.KEY_DD_SHEAR_VED)
    ow_vrdc = _dkv(c.KEY_DD_SHEAR_VRDC)
    ow_ur = ow_ved / ow_vrdc if ow_vrdc > 0 else None
    ow_ok = deck_rpt.get(c.KEY_DD_SHEAR_OK)
    ow_status = CheckStatus.PASS if ow_ok else CheckStatus.FAIL
    
    d_bot = _dkv(c.KEY_DD_D_BOT)
    k_factor = min(1.0 + (200.0 / d_bot)**0.5, 2.0) if d_bot > 0 else 0.0
    as_bot = _dkv(c.KEY_DD_AS_BOT)
    rho_l = min(as_bot / (1000.0 * d_bot), 0.02) if d_bot > 0 else 0.0
    
    shear = DeckShearCheck(
        punching_ved_kn=_qv(_dkv(c.KEY_DD_PUNCH_VED_KN), "kN"),
        punching_ved_mpa=_qv(punch_ved, "MPa"),
        punching_vrdc_mpa=_qv(punch_vrdc, "MPa"),
        punching_ur=punch_ur,
        punching_status=punch_status,
        oneway_ved=_qv(ow_ved, "kN/m"),
        oneway_size_factor_k=k_factor,
        oneway_rho_l=rho_l,
        oneway_vrdc=_qv(ow_vrdc, "kN/m"),
        oneway_ur=ow_ur,
        oneway_status=ow_status
    )
    
    # --- Crack Width Check ---
    wks = [_dkv(c.KEY_DD_WK_BOT), _dkv(c.KEY_DD_WK_TOP)]
    if has_oh:
        wks.append(_dkv(c.KEY_DD_WK_OH))
    gov_wk = max(wks)
    wk_lim = _dkv(c.KEY_DD_WK_LIMIT)
    wk_status = CheckStatus.PASS if gov_wk <= wk_lim else CheckStatus.FAIL
    
    crack_width = DeckCrackWidthCheck(
        calculated=_qv(gov_wk, "mm"),
        limit=_qv(wk_lim, "mm"),
        status=wk_status
    )
    
    # --- Detailing Check ---
    as_req_bot = _dkv(c.KEY_DD_AS_REQ_BOT)
    as_req_top = _dkv(c.KEY_DD_AS_REQ_TOP)
    as_min = _dkv(c.KEY_DD_AS_MIN)
    req_dist = max(0.20 * as_bot, as_min)
    
    as_prov_top = _dkv(c.KEY_DD_AS_TOP)
    as_prov_dist = _dkv(c.KEY_DD_AS_LONG)
    
    detailing = DeckDetailingCheck(
        required_bottom=_qv(as_req_bot, "mm^2/m"),
        provided_bottom=_qv(as_bot, "mm^2/m"),
        required_top=_qv(as_req_top, "mm^2/m"),
        provided_top=_qv(as_prov_top, "mm^2/m"),
        required_dist=_qv(req_dist, "mm^2/m"),
        provided_dist=_qv(as_prov_dist, "mm^2/m"),
        status_bottom=CheckStatus.PASS if as_bot >= as_req_bot else CheckStatus.FAIL,
        status_top=CheckStatus.PASS if as_prov_top >= as_req_top else CheckStatus.FAIL,
        status_dist=CheckStatus.PASS if as_prov_dist >= req_dist else CheckStatus.FAIL
    )
    
    return DeckDesignData(
        is_designed=True,
        loading=loading,
        flexure=flexure,
        shear=shear,
        crack_width=crack_width,
        detailing=detailing
    )

def _build_panel_data(pair: str, forces: dict, designs: dict) -> BracingPanelData:
    def build_member(member: str, force_type: str) -> BracingMemberCheck | None:
        pfx = "diag" if member == "diagonal" else "chord"
        key = f"{pfx}_{force_type}_kN"
        if forces.get(key) is None:
            return None
        
        gov_lc = forces.get(f"{pfx}_{force_type}_gov_lc")
        
        mem_designs = designs.get(member) or {}
        raw_design = mem_designs.get(force_type) or {}
        
        def _first(*keys):
            for k in keys:
                v = raw_design.get(k)
                if v is not None:
                    return v
            return None
            
        osdag = {}
        if raw_design:
            osdag = {
                "section":     _first("section_size.designation", "Optimum.Designation"),
                "capacity_kN": _first("Member.tension_capacity",  "Design.Strength"),
                "efficiency":  _first("Member.efficiency",        "Optimum.UR"),
                "slenderness": raw_design.get("Member.Slenderness"),
                "connection":  "Welded" if "Weld.Type" in raw_design else "Bolted",
            }
        
        dem_val = _qv(forces.get(key), "kN")
        cap_val = _qv(osdag.get("capacity_kN"), "kN")
        eff = osdag.get("efficiency")
        try:
            ur = float(eff) if eff is not None else None
            status = CheckStatus.PASS if ur is not None and ur <= 1.0 else (CheckStatus.FAIL if ur is not None else CheckStatus.UNAVAILABLE)
        except (TypeError, ValueError):
            ur = None
            status = CheckStatus.UNAVAILABLE
            
        return BracingMemberCheck(
            demand=dem_val,
            capacity=cap_val,
            ur=ur,
            status=status,
            governing_lc=str(gov_lc) if gov_lc else None,
            connection_type=str(osdag.get("connection")) if osdag.get("connection") else None,
            section=str(osdag.get("section")) if osdag.get("section") else None,
        )

    max_s_ur = None
    for member in ("diagonal", "chord"):
        lim = 400.0 if member == "chord" else 250.0
        for ft in ("compression", "tension"):
            mem_designs = designs.get(member) or {}
            raw_design = mem_designs.get(ft) or {}
            s = raw_design.get("Member.Slenderness")
            if s is not None:
                try:
                    ratio = float(s) / lim
                    if max_s_ur is None or ratio > max_s_ur:
                        max_s_ur = ratio
                except (TypeError, ValueError):
                    pass
    
    s_ur = max_s_ur
    s_status = CheckStatus.PASS if s_ur is not None and s_ur <= 1.0 else (CheckStatus.FAIL if s_ur is not None else CheckStatus.UNAVAILABLE)

    return BracingPanelData(
        pair_label=pair,
        diagonal_tension=build_member("diagonal", "tension"),
        diagonal_compression=build_member("diagonal", "compression"),
        chord_tension=build_member("chord", "tension"),
        chord_compression=build_member("chord", "compression"),
        slenderness_ur=s_ur,
        slenderness_status=s_status,
    )

def build_cross_bracing_data(output_dict: dict) -> CrossBracingData | None:
    forces_dict = output_dict.get("crossbracing_forces_dict") or {}
    designs_dict = output_dict.get("crossbracing_design_results") or {}
    
    pairs_data = forces_dict.get("pairs") or {}
    if not pairs_data:
        return None
        
    panels = []
    for pair_name in sorted(pairs_data.keys()):
        pair_forces = pairs_data[pair_name]
        pair_designs = designs_dict.get(pair_name) or {}
        panels.append(_build_panel_data(pair_name, pair_forces, pair_designs))
        
    return CrossBracingData(panels=tuple(panels))

def build_end_diaphragm_data(output_dict: dict, input_dict: dict) -> EndDiaphragmData | None:
    ed_type = ""
    for k, v in input_dict.items():
        if str(k).startswith(c.KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
            
    is_cb = "brac" in ed_type.strip().lower()
    panels = []
    
    if is_cb:
        forces_dict = output_dict.get("crossbracing_forces_dict") or {}
        designs_dict = output_dict.get("crossbracing_design_results") or {}
        pairs_data = forces_dict.get("pairs") or {}
        
        for pair_name in sorted(pairs_data.keys()):
            pair_forces = pairs_data[pair_name]
            pair_designs = designs_dict.get(pair_name) or {}
            panels.append(_build_panel_data(pair_name, pair_forces, pair_designs))
            
    return EndDiaphragmData(
        diaphragm_type=ed_type if ed_type else None,
        panels=tuple(panels),
        flexural_checks=None
    )

def build_overall_summary_data(
    girders: tuple[GirderDesignData, ...],
    deck: DeckDesignData | None,
    cb: CrossBracingData | None,
    ed: EndDiaphragmData | None,
    output_dict: dict,
) -> OverallSummaryData | None:
    # --- Girder Summary ---
    # Need to find the worst-case checks across all girders
    # The logic requires scanning per_lc / checks. We'll use output_dict['design_results']['per_girder']
    _pg_522 = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    
    def _dcr_row(label: str, check_ids: set, fallback_unit: str = "") -> SummaryCheckRecord:
        best = None
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in check_ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"), chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            
            # Find gov_lc
            gov_lc = None
            for _lc, _ld in (_pg_522.get(g, {}).get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"): continue
                for _chk in (_ld.get("checks") or []):
                    if _chk.get("id") in check_ids:
                        _d = _chk.get("dcr") or 0.0
                        if _d == d: # found it
                            gov_lc = str(_lc).strip()
                            break
                if gov_lc: break
            
            return SummaryCheckRecord(
                label=label,
                demand=_qv(dem, du or fallback_unit),
                capacity=_qv(cap, cu or fallback_unit),
                ur=d,
                status=CheckStatus.PASS if d <= 1.0 else CheckStatus.FAIL,
                governing_lc=gov_lc
            )
            
        # Fallback to per_lc
        best = None
        for g, gd in _pg_522.items():
            if str(g).startswith("EB"):
                continue
            for _lc, _ld in (gd.get("per_lc") or {}).items():
                if str(_lc).lower().startswith("envelope"): continue
                for chk in (_ld.get("checks") or []):
                    if chk.get("id") in check_ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), _lc)
        if best is not None:
            d, dem, cap, _lc = best
            return SummaryCheckRecord(
                label=label,
                demand=_qv(dem, fallback_unit),
                capacity=_qv(cap, fallback_unit),
                ur=d,
                status=CheckStatus.PASS if d <= 1.0 else CheckStatus.FAIL,
                governing_lc=str(_lc).strip()
            )
        
        return SummaryCheckRecord(label, None, None, None, CheckStatus.UNAVAILABLE, None)
        
    girder_records = (
        _dcr_row("Girder — Moment", {1}),
        _dcr_row("Girder — Shear", {2}),
        _dcr_row("Girder — LTB (constr.)", {5}),
        _dcr_row("Girder — Deflection", {13, 14}, "mm"),
        _dcr_row("Girder — Stress", {11}, "MPa"),
        _dcr_row("Girder — Fatigue", {8, 9}, "MPa"),
        _dcr_row("Transverse Shear (slab)", {16})
    )
    girders_max = max((r.ur for r in girder_records if r.ur is not None), default=None)
    girders_status = CheckStatus.PASS if girders_max is not None and girders_max <= 1.0 else (CheckStatus.FAIL if girders_max is not None else CheckStatus.UNAVAILABLE)
    if girders_max is not None:
        # Override component status based on the governing check's status
        for r in girder_records:
            if r.ur == girders_max:
                girders_status = r.status
                break
                
    girders_comp = ComponentSummary("Steel Plate Girders", girder_records, girders_max, girders_status)

    # --- Deck Summary ---
    def _dkv(k):
        dd = output_dict.get("deck_design_results") or {}
        try:
            return float(dd.get(k, 0))
        except (TypeError, ValueError):
            return 0.0
            
    _dk_has = bool(output_dict.get("deck_design_results"))
    def _deck_row(label, dem_key, cap_key, unit, is_oh=False):
        if not _dk_has:
            return SummaryCheckRecord(label, None, None, None, CheckStatus.UNAVAILABLE, None)
        
        _dk_oh = bool(output_dict.get("deck_design_results", {}).get(c.KEY_DD_M_ULS_OH))
        if is_oh and not _dk_oh:
             return SummaryCheckRecord(label, None, None, None, CheckStatus.UNAVAILABLE, None)
             
        dem = _dkv(dem_key)
        cap = _dkv(cap_key)
        ur = (dem / cap) if cap > 0 else None
        
        # Deck is designed for IRC:6 Basic ULS.
        gamma_dl = _dkv(c.KEY_DD_GAMMA_DL)
        gamma_ll = _dkv(c.KEY_DD_GAMMA_LL)
        deck_combo = f"Basic ULS: {gamma_dl:g}DL + {gamma_ll:g}LL"
        
        return SummaryCheckRecord(
            label=label,
            demand=_qv(dem, unit),
            capacity=_qv(cap, unit),
            ur=ur,
            status=CheckStatus.PASS if ur is not None and ur <= 1.0 else (CheckStatus.FAIL if ur is not None else CheckStatus.UNAVAILABLE),
            governing_lc=deck_combo
        )
        
    def _gov_sls_frequent():
        best = None
        for _g, _gd in _pg_522.items():
            if str(_g).startswith("EB"): continue
            for _lc, _ld in (_gd.get("per_lc") or {}).items():
                if "frequent" not in str(_lc).lower(): continue
                _d = _ld.get("max_dcr") or 0.0
                if best is None or _d > best[0]:
                    best = (_d, _lc)
        return str(best[1]).strip() if best else "Frequent SLS"

    cw_dem = max((_dkv(k) for k in [c.KEY_DD_WK_BOT, c.KEY_DD_WK_TOP, c.KEY_DD_WK_OH]), default=0.0)
    cw_cap = _dkv(c.KEY_DD_WK_LIMIT)
    cw_ur = (cw_dem / cw_cap) if cw_cap > 0 else None
    
    deck_records = (
        SummaryCheckRecord(
            label="Crack Width (slab)",
            demand=_qv(cw_dem, "mm") if _dk_has else None,
            capacity=_qv(cw_cap, "mm") if _dk_has else None,
            ur=cw_ur if _dk_has else None,
            status=(CheckStatus.PASS if cw_ur <= 1.0 else CheckStatus.FAIL) if _dk_has and cw_ur is not None else CheckStatus.UNAVAILABLE,
            governing_lc=_gov_sls_frequent() if _dk_has else None
        ),
        _deck_row("Deck — Flexure (sagging)", c.KEY_DD_M_ULS_SAG, c.KEY_DD_MU_BOT, "kN-m/m"),
        _deck_row("Deck — Flexure (hogging)", c.KEY_DD_M_ULS_HOG, c.KEY_DD_MU_TOP, "kN-m/m"),
        _deck_row("Deck — Cantilever Overhang", c.KEY_DD_M_ULS_OH, c.KEY_DD_MU_OH, "kN-m/m", True),
        _deck_row("Deck — Punching Shear", c.KEY_DD_PUNCH_VED, c.KEY_DD_VRD_C_MPA, "MPa"),
        _deck_row("Deck — One-Way Shear", c.KEY_DD_SHEAR_VED, c.KEY_DD_SHEAR_VRDC, "kN/m")
    )
    deck_max = max((r.ur for r in deck_records if r.ur is not None), default=None)
    deck_status = CheckStatus.PASS if deck_max is not None and deck_max <= 1.0 else (CheckStatus.FAIL if deck_max is not None else CheckStatus.UNAVAILABLE)
    if deck_max is not None:
        for r in deck_records:
            if r.ur == deck_max:
                deck_status = r.status
                break
                
    deck_comp = ComponentSummary("Concrete Deck Slab", deck_records, deck_max, deck_status)

    # --- Cross Bracing Summary ---
    def _cb_row(label: str, force_type: str, panels: tuple[BracingPanelData, ...]) -> SummaryCheckRecord:
        best_check = None
        for p in panels:
            for mem in (
                p.diagonal_tension if force_type == "tension" else p.diagonal_compression,
                p.chord_tension if force_type == "tension" else p.chord_compression
            ):
                if mem and mem.ur is not None:
                    if best_check is None or mem.ur > best_check.ur:
                        best_check = mem
        if best_check is None:
            return SummaryCheckRecord(label, None, None, None, CheckStatus.UNAVAILABLE, None)
            
        return SummaryCheckRecord(
            label=label,
            demand=best_check.demand,
            capacity=best_check.capacity,
            ur=best_check.ur,
            status=best_check.status,
            governing_lc=best_check.governing_lc
        )

    def _cb_slender_row(label: str, panels: tuple[BracingPanelData, ...]) -> SummaryCheckRecord:
        best_ur = None
        best_status = CheckStatus.UNAVAILABLE
        for p in panels:
            if p.slenderness_ur is not None:
                if best_ur is None or p.slenderness_ur > best_ur:
                    best_ur = p.slenderness_ur
                    best_status = p.slenderness_status
        return SummaryCheckRecord(label, None, None, best_ur, best_status, None)

    cb_comp = None
    if cb and cb.panels:
        cb_records = (
            _cb_row("Cross Bracing — Compression", "compression", cb.panels),
            _cb_row("Cross Bracing — Tension", "tension", cb.panels),
            _cb_slender_row("Cross Bracing — Slenderness", cb.panels)
        )
        cb_max = max((r.ur for r in cb_records if r.ur is not None), default=None)
        cb_status = CheckStatus.PASS if cb_max is not None and cb_max <= 1.0 else (CheckStatus.FAIL if cb_max is not None else CheckStatus.UNAVAILABLE)
        if cb_max is not None:
            for r in cb_records:
                if r.ur == cb_max:
                    cb_status = r.status
                    break
        cb_comp = ComponentSummary("Cross Bracing", cb_records, cb_max, cb_status)

    # --- End Diaphragm Summary ---
    ed_comp = None
    if ed:
        if ed.panels:
            ed_records = (
                _cb_row("End Diaphragm — Compression", "compression", ed.panels),
                _cb_row("End Diaphragm — Tension", "tension", ed.panels),
            )
            ed_max = max((r.ur for r in ed_records if r.ur is not None), default=None)
            ed_status = CheckStatus.PASS if ed_max is not None and ed_max <= 1.0 else (CheckStatus.FAIL if ed_max is not None else CheckStatus.UNAVAILABLE)
            if ed_max is not None:
                for r in ed_records:
                    if r.ur == ed_max:
                        ed_status = r.status
                        break
            ed_comp = ComponentSummary("End Diaphragms", ed_records, ed_max, ed_status)
        else:
            # Emulate legacy report: Rolled / Welded section — design to be added
            ed_records = (
                SummaryCheckRecord("End Diaphragm — Moment", None, None, None, CheckStatus.UNAVAILABLE, None),
                SummaryCheckRecord("End Diaphragm — Shear", None, None, None, CheckStatus.UNAVAILABLE, None)
            )
            ed_comp = ComponentSummary("End Diaphragms", ed_records, None, CheckStatus.UNAVAILABLE)

    return OverallSummaryData(
        girders=girders_comp,
        deck=deck_comp,
        cross_bracing=cb_comp,
        end_diaphragm=ed_comp
    )

def build_design_check_data(
    output_dict: dict,
    input_dict: dict,
) -> DesignCheckData:
    """Build the complete DesignCheckData hierarchy."""
    girders = build_girder_design_data(output_dict, input_dict)
    sc_data = build_shear_connector_data(output_dict, input_dict)
    dk_data = build_deck_design_data(output_dict, input_dict)
    cb_data = build_cross_bracing_data(output_dict)
    ed_data = build_end_diaphragm_data(output_dict, input_dict)
    summary_data = build_overall_summary_data(girders, dk_data, cb_data, ed_data, output_dict)
    
    return DesignCheckData(
        girders=girders,
        shear_connectors=sc_data,
        deck=dk_data,
        cross_bracing=cb_data,
        end_diaphragm=ed_data,
        summary=summary_data
    )
