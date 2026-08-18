"""Extraction functions for design check data (Chapter 5).

Phase 5A: girder design tables (5.1–5.13) only.
"""

from __future__ import annotations

from typing import Dict, List, Optional

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
) -> DesignCheckData:
    """Extract girder design check data from output_dict + input_dict.

    Phase 5A: produces GirderDesignData for Tables 5.1–5.13 only.
    """
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

    return DesignCheckData(girders=tuple(girders))
