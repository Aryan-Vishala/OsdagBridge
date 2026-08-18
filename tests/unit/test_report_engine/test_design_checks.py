"""Tests for Phase 5A: GirderDesignData extraction (build_girder_design_data)."""

import pytest

from osdagbridge.core.report_engine.facts import (
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
from osdagbridge.core.report_engine.facts.design_checks import (
    _ge_status,
    _interaction_status,
    _parse_status_string,
    _safe_float,
    _ur_status,
    build_girder_design_data,
    build_design_check_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _base_output_dict(**overrides) -> dict:
    """Minimal output_dict with one girder's section properties."""
    base = {
        "steeldesign.details.total_depth": 1500,
        "steeldesign.details.top_flange_width": 400,
        "steeldesign.details.bottom_flange_width": 600,
        "steeldesign.details.top_flange_thickness": 25,
        "steeldesign.details.bottom_flange_thickness": 40,
        "steeldesign.details.web_thickness": 12,
        "steeldesign.details.section_properties.area": 196.8,
        "steeldesign.details.section_properties.iz": 1067153,
        "steeldesign.details.section_properties.zz": 14228,
        "steeldesign.details.section_properties.zuz": 16810,
        "steeldesign.details.effective_slab_width": 1400,
        "steeldesign.details.section_properties.composite_iz": 1850000,
        "steeldesign.details.section_properties.pna_depth": 850,
        "steeldesign.details.classification.flange_slenderness": 7.0,
        "steeldesign.details.classification.flange_class_limit": 9.4,
        "steeldesign.details.classification.flange_class": "1",
        "steeldesign.details.classification.web_slenderness": 110.0,
        "steeldesign.details.classification.web_class_limit": 84.0,
        "steeldesign.details.classification.web_class": "4",
        "steeldesign.details.section_class": "Class 4",
        "steeldesign.details.moment.mu_applied": 2500.0,
        "steeldesign.details.moment.md_capacity": 3200.0,
        "util.flexure": 78.1,  # percent: 78.1/100 = 0.781
        "steeldesign.details.shear_check.vu_applied": 450.0,
        "steeldesign.details.shear_check.av_area": 18000.0,
        "steeldesign.details.shear_check.panel_cd": 0.85,
        "steeldesign.details.shear_check.kv": 5.35,
        "steeldesign.details.shear_check.lambda_w": 0.62,
        "steeldesign.details.shear_check.tau_b": 120.5,
        "steeldesign.details.shear_check.vcr": 980.0,
        "util.shear": 45.9,  # percent
        "steeldesign.details.interaction.high_shear": "No",
        "steeldesign.details.interaction.mdv": 3100.0,
        "util.interaction": 81.2,  # percent
        "steeldesign.details.interaction.mn_axial": None,
        "steeldesign.details.interaction.mn_moment": None,
        "steeldesign.details.interaction.mn_ratio": None,
        "steeldesign.details.ltb.mcr": 5600.0,
        "steeldesign.details.ltb.lambda_lt": 0.76,
        "steeldesign.details.ltb.chi_lt": 0.83,
        "steeldesign.details.ltb.mb": 4650.0,
        "util.ltb": 53.8,  # percent
        "steeldesign.details.stiffener_summary.method": "Yield",
        "steeldesign.details.stiffener_summary.int_thickness": 12.0,
        "steeldesign.details.stiffener_summary.int_spacing": 1500.0,
        "steeldesign.details.stiffener_summary.end_thickness": 16.0,
        "steeldesign.details.stiffener_summary.end_count": 2,
        "steeldesign.details.stiffener_summary.longitudinal": "None",
        "steeldesign.details.bearing_stiffener.reaction": 800.0,
        "steeldesign.details.bearing_stiffener.fcdw_wb": 950.0,
        "steeldesign.details.bearing_stiffener.fcdw_lc": 1100.0,
        "steeldesign.details.bearing_stiffener.fpsd": 870.0,
        "steeldesign.details.bearing_stiffener.fcd": 920.0,
        "design_results": {
            "steeldesign.stress.steel": 210.5,
            "steeldesign.stress.steel.allowable": 256.5,
            "steeldesign.uls_per_girder": {
                "fatigue": {
                    "G1": {
                        "demand": 80.2,
                        "capacity": 125.0,
                        "ur": 0.64,
                        "status": "PASS",
                    },
                },
            },
            "per_girder": {
                "G1": {
                    "checks": [
                        {"name": "Flexure", "dcr": 0.78, "check_id": "flexure",
                         "status": "PASS", "demand": 2500.0, "demand_unit": "kN-m",
                         "capacity": 3200.0, "capacity_unit": "kN-m"},
                        {"name": "Shear", "dcr": 0.46, "check_id": "shear",
                         "status": "PASS", "demand": 450.0, "demand_unit": "kN",
                         "capacity": 980.0, "capacity_unit": "kN"},
                    ],
                    "per_lc": {
                        "Envelope ULS": {
                            "checks": [
                                {"id": "flexure", "dcr": 0.78},
                                {"id": "shear", "dcr": 0.46},
                            ],
                        },
                        "LC1": {
                            "checks": [
                                {"id": "flexure", "dcr": 0.72},
                                {"id": "shear", "dcr": 0.40},
                            ],
                        },
                        "LC2": {
                            "checks": [
                                {"id": "flexure", "dcr": 0.78},
                                {"id": "shear", "dcr": 0.46},
                            ],
                        },
                    },
                    "demand": {"governing_combination": "LC2"},
                },
            },
        },
    }
    base.update(overrides)
    return base


def _base_input_dict() -> dict:
    return {
        "typical_section.no_of_girders": 1,
        "geometry.span": 30.0,
        "geometry.design_mode": "Optimized",
        "typical_section.member_properties.girder_details.select_girder.G1": "G1",
        "typical_section.member_properties.girder_details.member_id.G1.M1": "G1M1",
    }


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelperFunctions:
    def test_safe_float_normal(self):
        assert _safe_float(42.5) == 42.5

    def test_safe_float_string(self):
        assert _safe_float("3.14") == 3.14

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_invalid(self):
        assert _safe_float("abc") is None

    def test_interaction_status_pass(self):
        assert _interaction_status(0.85) == CheckStatus.PASS

    def test_interaction_status_warn(self):
        assert _interaction_status(0.95) == CheckStatus.WARN

    def test_interaction_status_fail(self):
        assert _interaction_status(1.05) == CheckStatus.FAIL

    def test_interaction_status_none(self):
        assert _interaction_status(None) == CheckStatus.UNAVAILABLE

    def test_ur_status_pass(self):
        assert _ur_status(1.0) == CheckStatus.PASS

    def test_ur_status_fail(self):
        assert _ur_status(1.1) == CheckStatus.FAIL

    def test_ge_status_pass(self):
        assert _ge_status(100.0, 80.0) == CheckStatus.PASS

    def test_ge_status_fail(self):
        assert _ge_status(70.0, 80.0) == CheckStatus.FAIL

    def test_parse_status_pass(self):
        assert _parse_status_string("PASS") == CheckStatus.PASS

    def test_parse_status_fail(self):
        assert _parse_status_string("FAIL") == CheckStatus.FAIL

    def test_parse_status_none(self):
        assert _parse_status_string(None) == CheckStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Single girder extraction
# ---------------------------------------------------------------------------

class TestBuildGirderDesignData:
    def test_returns_design_check_data(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert isinstance(result, DesignCheckData)

    def test_single_girder(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert len(result.girders) == 1
        assert isinstance(result.girders[0], GirderDesignData)
        assert result.girders[0].girder_label == "G1"

    def test_section_properties_values(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sp = result.girders[0].section_properties
        assert sp.depth.value == 1500
        assert sp.depth.unit == "mm"
        assert sp.top_flange_width.value == 400
        assert sp.bottom_flange_width.value == 600
        assert sp.gross_area.value == 196.8
        assert sp.gross_area.unit == "cm\u00b2"
        assert sp.moment_of_inertia.value == 1067153
        assert sp.pna_depth.value == 850

    def test_classification_values(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        cl = result.girders[0].classification
        assert cl.flange_slenderness == 7.0
        assert cl.class_flange == "1"
        assert cl.web_slenderness == 110.0
        assert cl.class_web == "4"
        assert cl.section_class == "Class 4"

    def test_flexure_check_ur_converted(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        fl = result.girders[0].flexure
        assert fl.mu_applied.value == 2500.0
        assert fl.mu_applied.unit == "kN-m"
        assert fl.md_capacity.value == 3200.0
        assert abs(fl.utilization_ratio - 0.781) < 0.001
        assert fl.status == CheckStatus.PASS

    def test_shear_check_ur_converted(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sh = result.girders[0].shear
        assert sh.vu.value == 450.0
        assert sh.vu.unit == "kN"
        assert abs(sh.utilization_ratio - 0.459) < 0.001
        assert sh.status == CheckStatus.PASS

    def test_interaction_check_three_bands(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        ix = result.girders[0].interaction
        assert ix.high_shear == "No"
        assert ix.mdv.value == 3100.0
        assert abs(ix.mv_ur - 0.812) < 0.001
        assert ix.mv_status == CheckStatus.PASS
        assert ix.mn_ratio is None
        assert ix.mn_status == CheckStatus.UNAVAILABLE

    def test_ltb_check_three_bands(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        lt = result.girders[0].ltb
        assert lt.mcr.value == 5600.0
        assert lt.ltb_lambda == 0.76
        assert lt.ltb_chi == 0.83
        assert abs(lt.utilization_ratio - 0.538) < 0.001
        assert lt.status == CheckStatus.PASS

    def test_stiffener_summary_values(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        st = result.girders[0].stiffener_summary
        assert st.method == "Yield"
        assert st.int_thick.value == 12.0
        assert st.int_spacing.value == 1500.0
        assert st.end_count == 2
        assert st.long_stiff == "None"

    def test_bearing_stiffener_checks(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        bs = result.girders[0].bearing_stiffener
        assert bs.wb_req.value == 800.0
        assert bs.wb_prov.value == 950.0
        assert bs.wb_status == CheckStatus.PASS
        assert bs.lc_prov.value == 1100.0
        assert bs.ps_prov.value == 870.0
        assert bs.cb_prov.value == 920.0

    def test_deflection_check_computed(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        df = result.girders[0].deflection
        assert df.allow_live.value == 30000.0 / 800.0
        assert df.allow_total.value == 30000.0 / 600.0

    def test_stress_check_from_nested_dict(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        st = result.girders[0].stress
        assert st.actual_stress.value == 210.5
        assert st.allowable_stress.value == 256.5
        assert st.status == CheckStatus.PASS

    def test_fatigue_check_from_nested_dict(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        fa = result.girders[0].fatigue
        assert fa.stress_range.value == 80.2
        assert fa.fatigue_limit.value == 125.0
        assert abs(fa.utilization_ratio - 0.64) < 0.01
        assert fa.status == CheckStatus.PASS

    def test_summary_highest_dcr(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sm = result.girders[0].summary
        assert sm.controlling_check == "Flexure"
        assert abs(sm.dcr - 0.78) < 0.01
        assert sm.governing_lc == "LC2"
        assert sm.status == CheckStatus.PASS

    def test_summary_skips_envelope_lc(self):
        """The controlling LC should be a real LC, not the Envelope."""
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sm = result.girders[0].summary
        assert "Envelope" not in sm.governing_lc


# ---------------------------------------------------------------------------
# Multiple girder extraction
# ---------------------------------------------------------------------------

class TestMultipleGirders:
    def test_two_girders(self):
        od = _base_output_dict()
        od["typical_section.no_of_girders"] = 2
        # Add girder labels via input_dict keys
        od["typical_section.member_properties.girder_details.select_girder.G2"] = "G2"
        od["typical_section.member_properties.girder_details.member_id.G2.M1"] = "G2M1"
        # Add per-girder fatigue and summary for G2
        od["design_results"]["steeldesign.uls_per_girder"]["fatigue"]["G2"] = {
            "demand": 90.0, "capacity": 125.0, "ur": 0.72, "status": "PASS",
        }
        od["design_results"]["per_girder"]["G2"] = {
            "checks": [
                {"name": "Flexure", "dcr": 0.85, "check_id": "flexure",
                 "status": "PASS", "demand": 2700.0, "demand_unit": "kN-m",
                 "capacity": 3200.0, "capacity_unit": "kN-m"},
            ],
            "per_lc": {
                "LC3": {"checks": [{"id": "flexure", "dcr": 0.85}]},
            },
            "demand": {"governing_combination": "LC3"},
        }
        # Add deflection for G2
        od["steeldesign.deflection.live_mm.G2"] = 20.0
        od["steeldesign.deflection.total_mm.G2"] = 35.0

        id = _base_input_dict()
        id["typical_section.no_of_girders"] = 2

        result = build_design_check_data(od, id)
        assert len(result.girders) == 2
        assert result.girders[0].girder_label == "G1"
        assert result.girders[1].girder_label == "G2"
        assert result.girders[1].fatigue.stress_range.value == 90.0
        assert result.girders[1].summary.controlling_check == "Flexure"


# ---------------------------------------------------------------------------
# Conditional Table 5.8
# ---------------------------------------------------------------------------

class TestConditionalIntermediateStiffener:
    def test_optimized_mode_no_intermediate_stiffener(self):
        od = _base_output_dict()
        id = _base_input_dict()
        id["geometry.design_mode"] = "Optimized"
        result = build_design_check_data(od, id)
        assert result.girders[0].intermediate_stiffener is None

    def test_custom_mode_with_intermediate_stiffener(self):
        od = _base_output_dict()
        od["steeldesign.details.int_stiffener.iys_min"] = 500000.0
        od["steeldesign.details.int_stiffener.iys_prov"] = 650000.0
        od["steeldesign.details.int_stiffener.fq"] = 120.0
        od["steeldesign.details.int_stiffener.fqd"] = 150.0
        id = _base_input_dict()
        id["geometry.design_mode"] = "Custom"
        result = build_design_check_data(od, id)
        ist = result.girders[0].intermediate_stiffener
        assert ist is not None
        assert ist.iys_prov.value == 650000.0
        assert ist.iys_status == CheckStatus.PASS
        assert ist.fqd_status == CheckStatus.PASS


# ---------------------------------------------------------------------------
# Missing / None values
# ---------------------------------------------------------------------------

class TestMissingValues:
    def test_empty_output_dict(self):
        result = build_design_check_data({}, _base_input_dict())
        assert len(result.girders) == 1
        g = result.girders[0]
        assert g.section_properties.depth is None
        assert g.flexure.utilization_ratio is None
        assert g.flexure.status == CheckStatus.UNAVAILABLE

    def test_zero_ur_is_valid(self):
        od = _base_output_dict(**{"util.flexure": 0.0})
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert result.girders[0].flexure.utilization_ratio == 0.0
        assert result.girders[0].flexure.status == CheckStatus.PASS

    def test_none_ur_is_unavailable(self):
        od = _base_output_dict(**{"util.flexure": None})
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert result.girders[0].flexure.utilization_ratio is None
        assert result.girders[0].flexure.status == CheckStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Interaction WARN band
# ---------------------------------------------------------------------------

class TestInteractionBands:
    def test_warn_band_for_interaction(self):
        od = _base_output_dict(**{"util.interaction": 95.0})  # 0.95 ratio
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert result.girders[0].interaction.mv_status == CheckStatus.WARN

    def test_fail_band_for_ltb(self):
        od = _base_output_dict(**{"util.ltb": 105.0})  # 1.05 ratio
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        assert result.girders[0].ltb.status == CheckStatus.FAIL


# ---------------------------------------------------------------------------
# Bearing stiffener: 0.0 or None → UNAVAILABLE
# ---------------------------------------------------------------------------

class TestBearingStiffenerEdgeCases:
    def test_zero_resistance_unavailable(self):
        od = _base_output_dict(**{
            "steeldesign.details.bearing_stiffener.fcdw_wb": 0.0,
        })
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        bs = result.girders[0].bearing_stiffener
        assert bs.wb_status == CheckStatus.UNAVAILABLE

    def test_none_reaction_unavailable(self):
        od = _base_output_dict(**{
            "steeldesign.details.bearing_stiffener.reaction": None,
        })
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        bs = result.girders[0].bearing_stiffener
        assert bs.wb_status == CheckStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Summary edge cases
# ---------------------------------------------------------------------------

class TestSummaryEdgeCases:
    def test_empty_checks(self):
        od = _base_output_dict()
        od["design_results"]["per_girder"]["G1"]["checks"] = []
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sm = result.girders[0].summary
        assert sm.status == CheckStatus.UNAVAILABLE

    def test_no_per_lc(self):
        od = _base_output_dict()
        od["design_results"]["per_girder"]["G1"]["per_lc"] = {}
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        sm = result.girders[0].summary
        assert sm.governing_lc == ""


# ---------------------------------------------------------------------------
# Frozen / immutable
# ---------------------------------------------------------------------------

class TestFrozenDesignData:
    def test_girder_design_data_frozen(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        with pytest.raises(AttributeError):
            result.girders[0].girder_label = "Changed"

    def test_design_check_data_frozen(self):
        od = _base_output_dict()
        id = _base_input_dict()
        result = build_design_check_data(od, id)
        with pytest.raises(AttributeError):
            result.girders = ()
